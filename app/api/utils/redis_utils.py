from typing import Any, List, Mapping

from aioredis.connection import EncodableT

from app.api.utils import exception_utils
from app.core import config
from app.db.db import RedisDBManager

logger = config.get_logstash_logger(__name__)


async def set_hmap(
    request_id: str,
    redisdb: RedisDBManager,
    key_name: str,
    value: Mapping[Any, EncodableT],
    should_expire: bool,
    expire_time: int = 5,
):
    try:
        await redisdb.connection.hset(name=key_name, mapping=value)
        if should_expire:
            await redisdb.connection.expire(key_name, time=expire_time)
    except Exception as e:
        exception_utils.log_and_raise_exception(
            "Redis exception",
            request_id,
            str(e),
            "Internal Server Error",
        )


async def get_hmap(
    request_id: str,
    redis_db: RedisDBManager,
    key_name: str,
    sub_keys: List[str],
):
    try:
        value = await redis_db.connection.hmget(
            name=key_name,
            keys=sub_keys,
        )
        return value
    except Exception as e:
        exception_utils.log_and_raise_exception(
            "Redis exception",
            request_id,
            str(e),
            "Internal Server Error",
        )


async def hgetall(
    request_id: str,
    redis_db: RedisDBManager,
    key_name: str,
):
    try:
        value = await redis_db.connection.hgetall(name=key_name)
        return value
    except Exception as e:
        print(str(e))
        exception_utils.log_and_raise_exception(
            "Redis exception",
            request_id,
            str(e),
            "Internal Server Error",
        )
