import logging

from django.conf import settings

import redis


logger = logging.getLogger('tg_pubsub')


def create_redis_connection():
    redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
    redis_port = getattr(settings, 'REDIS_PORT', 6379)
    redis_db = getattr(settings, 'REDIS_DB', 0)

    # NB: for pubsub, the database number doesn't matter. At all.
    r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
    try:
        r.ping()
    except redis.exceptions.ConnectionError as e:
        logger.warning("Redis isn't available, pubsub will be disabled: %s", e)
        return None

    logger.info("Connected to Redis")
    return r


redis_connection = create_redis_connection()


def publish(channel, message):
    if redis_connection is None:
        return

    try:
        redis_connection.publish(channel, message)
    except redis.exceptions.ConnectionError as e:
        logger.warning("Redis seems to have died: %s", e)
