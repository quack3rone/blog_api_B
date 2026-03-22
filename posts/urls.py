from django.urls import path

from posts.views import PostDetailView, PostListCreateView

urlpatterns = [
    path("", PostListCreateView.as_view(), name="post-list-create",),

    path("<int:post_id>/", PostDetailView.as_view(), name="post-detail",),
]