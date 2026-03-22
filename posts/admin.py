from django.contrib import admin
from posts.models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_at", "updated_at")
    
    list_display_links = ("id", "title")
    
    search_fields = ("title", "content")
    
    list_filter = ("created_at",)