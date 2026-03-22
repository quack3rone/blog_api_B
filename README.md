# Blog Cache API

REST API для блога с кешированием постов в Redis.

**Стек:** Python, Django, Django REST Framework, PostgreSQL, Redis

## Архитектура
-

## Эндпоинты

| Метод  | URL                | Описание                    | Код ответа           |
|--------|--------------------|-----------------------------|----------------------|
| GET    | `/api/posts/`      | Список всех постов          | 200 OK               |
| POST   | `/api/posts/`      | Создать новый пост          | 201 Created          |
| GET    | `/api/posts/{id}/` | Получить пост (с кешем)     | 200 OK / 404         |
| PUT    | `/api/posts/{id}/` | Обновить пост               | 200 OK / 400 / 404   |
| DELETE | `/api/posts/{id}/` | Удалить пост                | 204 No Content / 404 |

### Примеры запросов
-