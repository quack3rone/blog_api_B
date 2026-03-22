from django.db import models


class Post(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name="Заголовок"
    )

    content = models.TextField(
        verbose_name="Содержание"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Дата создания"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title