import logging

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from posts.cache import get_post_from_cache, invalidate_post_cache, set_post_to_cache
from posts.models import Post
from posts.serializers import PostSerializer


logger = logging.getLogger(__name__)


class PostListCreateView(APIView):
    def get(self, request):
        posts = Post.objects.all()

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(posts, request)

        serializer = PostSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = PostSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            logger.info("Post created with id: %s", serializer.data["id"])

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        logger.warning("Post creation failed, errors: %s", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostDetailView(APIView):
    def _get_post_or_404(self, post_id):
        try:
            return Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            return None

    def get(self, request, post_id):
        cached_data = get_post_from_cache(post_id)

        if cached_data is not None:
            logger.info("Cache hit for post id: %s", post_id)
            return Response(cached_data, status=status.HTTP_200_OK)

        logger.info("Cache miss for post id: %s, querying database", post_id)
        post = self._get_post_or_404(post_id)

        if post is None:
            return Response(
                {"detail": "Пост не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PostSerializer(post)

        set_post_to_cache(post_id, serializer.data)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, post_id):
        post = self._get_post_or_404(post_id)

        if post is None:
            return Response(
                {"detail": "Пост не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PostSerializer(post, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            invalidate_post_cache(post_id)

            logger.info("Post partially updated, id: %s, cache invalidated", post_id)

            return Response(serializer.data, status=status.HTTP_200_OK)

        logger.warning("Post patch failed, id: %s, errors: %s", post_id, serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, post_id):
        post = self._get_post_or_404(post_id)

        if post is None:
            return Response(
                {"detail": "Пост не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PostSerializer(post, data=request.data)

        if serializer.is_valid():
            serializer.save()

            invalidate_post_cache(post_id)

            logger.info("Post updated, id: %s, cache invalidated", post_id)

            return Response(serializer.data, status=status.HTTP_200_OK)

        logger.warning("Post update failed, id: %s, errors: %s", post_id, serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, post_id):
        post = self._get_post_or_404(post_id)

        if post is None:
            return Response(
                {"detail": "Пост не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        deleted_post_id = post.id
        post.delete()

        invalidate_post_cache(deleted_post_id)

        logger.info("Post deleted, id: %s, cache invalidated", deleted_post_id)

        return Response(status=status.HTTP_204_NO_CONTENT)