import json

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from posts.cache import CACHE_KEY_PREFIX
from posts.models import Post


@pytest.fixture()
def api_client():
    client = APIClient()
    yield client
    cache.clear()


@pytest.fixture()
def sample_post():
    post = Post.objects.create(
        title="Тестовый пост",
        content="Содержание тестового поста",
    )
    return post


def _get_cache_key(post_id):
    return f"{CACHE_KEY_PREFIX}:{post_id}"


# test 1: Cache miss/cache hit
@pytest.mark.django_db
class TestCacheMissAndHit:

    def test_first_get_is_cache_miss(self, api_client, sample_post):
        cache_key = _get_cache_key(sample_post.id)
        assert cache.get(cache_key) is None

        url = reverse("post-detail", kwargs={"post_id": sample_post.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == sample_post.id
        assert response.data["title"] == "Тестовый пост"
        assert response.data["content"] == "Содержание тестового поста"

        cached_data = cache.get(cache_key)
        assert cached_data is not None

        cached_post = json.loads(cached_data)
        assert cached_post["id"] == sample_post.id
        assert cached_post["title"] == "Тестовый пост"

    def test_second_get_is_cache_hit(self, api_client, sample_post):
        url = reverse("post-detail", kwargs={"post_id": sample_post.id})

        api_client.get(url)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == sample_post.id
        assert response.data["title"] == "Тестовый пост"

        cache_key = _get_cache_key(sample_post.id)
        assert cache.get(cache_key) is not None


# test 2: инвалидация (put/обновление)
@pytest.mark.django_db
class TestCacheInvalidationOnUpdate:

    def test_put_invalidates_cache(self, api_client, sample_post):
        detail_url = reverse("post-detail", kwargs={"post_id": sample_post.id})
        cache_key = _get_cache_key(sample_post.id)

        api_client.get(detail_url)
        assert cache.get(cache_key) is not None

        update_data = {
            "title": "Обновлённый заголовок",
            "content": "Обновлённое содержание",
        }
        response = api_client.put(detail_url, data=update_data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Обновлённый заголовок"
        assert cache.get(cache_key) is None

        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Обновлённый заголовок"

        cached_data = cache.get(cache_key)
        assert cached_data is not None

        cached_post = json.loads(cached_data)
        assert cached_post["title"] == "Обновлённый заголовок"


# test 2b: инвалидация (patch/частичное обновление)
@pytest.mark.django_db
class TestCacheInvalidationOnPatch:

    def test_patch_invalidates_cache(self, api_client, sample_post):
        detail_url = reverse("post-detail", kwargs={"post_id": sample_post.id})
        cache_key = _get_cache_key(sample_post.id)

        api_client.get(detail_url)
        assert cache.get(cache_key) is not None

        response = api_client.patch(detail_url, data={"title": "Патч заголовка"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Патч заголовка"
        assert response.data["content"] == "Содержание тестового поста"
        assert cache.get(cache_key) is None

        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Патч заголовка"

        cached_data = cache.get(cache_key)
        assert cached_data is not None
        cached_post = json.loads(cached_data)
        assert cached_post["title"] == "Патч заголовка"

    def test_patch_nonexistent_post_returns_404(self, api_client):
        url = reverse("post-detail", kwargs={"post_id": 99999})
        response = api_client.patch(url, data={"title": "Новый"}, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_patch_partial_fields_only(self, api_client, sample_post):
        detail_url = reverse("post-detail", kwargs={"post_id": sample_post.id})

        response = api_client.patch(detail_url, data={"title": "Только заголовок"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Только заголовок"
        assert response.data["content"] == "Содержание тестового поста"


# test 3: инвалидация (delete)
@pytest.mark.django_db
class TestCacheInvalidationOnDelete:

    def test_delete_invalidates_cache(self, api_client, sample_post):
        detail_url = reverse("post-detail", kwargs={"post_id": sample_post.id})
        cache_key = _get_cache_key(sample_post.id)

        api_client.get(detail_url)
        assert cache.get(cache_key) is not None

        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert cache.get(cache_key) is None

        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# test 4: 404 на несуществующий
@pytest.mark.django_db
class TestPostNotFound:

    def test_get_nonexistent_post_returns_404(self, api_client):
        url = reverse("post-detail", kwargs={"post_id": 99999})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "Пост не найден."

    def test_put_nonexistent_post_returns_404(self, api_client):
        url = reverse("post-detail", kwargs={"post_id": 99999})
        response = api_client.put(url, data={"title": "Новый", "content": "Текст"}, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_post_returns_404(self, api_client):
        url = reverse("post-detail", kwargs={"post_id": 99999})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


# test 5: создание поста (post)
@pytest.mark.django_db
class TestPostCreation:

    def test_create_post_success(self, api_client):
        url = reverse("post-list-create")
        post_data = {
            "title": "Новый пост",
            "content": "Содержание нового поста",
        }

        response = api_client.post(url, data=post_data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "Новый пост"
        assert response.data["content"] == "Содержание нового поста"
        assert "id" in response.data
        assert "created_at" in response.data
        assert "updated_at" in response.data
        assert Post.objects.filter(id=response.data["id"]).exists()

    def test_create_post_invalid_data(self, api_client):
        url = reverse("post-list-create")
        response = api_client.post(url, data={"title": "", "content": ""}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "title" in response.data
        assert "content" in response.data


# test 6: список постов (get)
@pytest.mark.django_db
class TestPostList:

    def test_get_empty_list(self, api_client):
        url = reverse("post-list-create")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["results"] == []

    def test_get_list_with_posts(self, api_client, sample_post):
        url = reverse("post-list-create")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == sample_post.id


# test 7: пагинация
@pytest.mark.django_db
class TestPagination:

    def test_pagination_next_exists_when_more_than_page_size(self, api_client):
        for i in range(11):
            Post.objects.create(title=f"Пост {i}", content="Содержание")

        url = reverse("post-list-create")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 11
        assert len(response.data["results"]) == 10
        assert response.data["next"] is not None
        assert response.data["previous"] is None

    def test_pagination_no_next_when_fits_on_one_page(self, api_client):
        for i in range(3):
            Post.objects.create(title=f"Пост {i}", content="Содержание")

        url = reverse("post-list-create")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3
        assert response.data["next"] is None