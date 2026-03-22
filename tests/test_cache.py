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


# test 5: создание поста (POST)
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


# test 6: список постов (GET)
@pytest.mark.django_db
class TestPostList:

    def test_get_empty_list(self, api_client):
        url = reverse("post-list-create")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_get_list_with_posts(self, api_client, sample_post):
        url = reverse("post-list-create")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == sample_post.id