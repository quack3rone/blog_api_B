import json
import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "post"

CACHE_TTL = 300


def _make_cache_key(post_id):
    return f"{CACHE_KEY_PREFIX}:{post_id}"


def get_post_from_cache(post_id):
    key = _make_cache_key(post_id)

    try:
        cached_data = cache.get(key)

        if cached_data is not None:
            logger.debug("Cache hit for key: %s", key)
            return json.loads(cached_data)

        logger.debug("Cache miss for key: %s", key)
        return None

    except Exception as e:
        logger.error("Redis error on GET key %s: %s", key, str(e))
        return None


def set_post_to_cache(post_id, post_data):
    key = _make_cache_key(post_id)

    try:
        json_data = json.dumps(post_data, ensure_ascii=False)
        cache.set(key, json_data, CACHE_TTL)

        logger.debug("Cached post with key: %s, TTL: %s", key, CACHE_TTL)

    except Exception as e:
        logger.error("Redis error on SET key %s: %s", key, str(e))


def invalidate_post_cache(post_id):
    key = _make_cache_key(post_id)

    try:
        cache.delete(key)

        logger.debug("Invalidated cache for key: %s", key)

    except Exception as e:
        logger.error("Redis error on DELETE key %s: %s", key, str(e))