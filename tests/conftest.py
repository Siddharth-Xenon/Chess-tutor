import asyncio
import uuid
from os import environ as env

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from fastapi_jwt_auth.auth_jwt import AuthJWT

from app.db.db import MongoDBManager, RedisDBManager

load_dotenv(".env")
# when using async fixtures with scope above function
# the eventloop fixture needs to be redefined
# https://github.com/tortoise/tortoise-orm/issues/638


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def create_token():
    jwtclient = AuthJWT()
    token = jwtclient.create_access_token(subject="1234")
    return token


class TestMongoDBManager(MongoDBManager):
    async def connect_to_database(self, path: str, dbname: str):
        await super().connect_to_database(path, dbname)


mongo = TestMongoDBManager()
redis = RedisDBManager()


async def clear_mongo_db():
    pass


@pytest_asyncio.fixture(scope="session", autouse=True)
async def start_close_clear_db():
    id = str(uuid.uuid4())[:26]
    mongo_db = "TEST_DB_SI_" + id

    await mongo.connect_to_database(env.get("MONGO_TEST_CONN_STR"), mongo_db)
    await clear_mongo_db()

    yield

    await clear_mongo_db()
    await mongo.database.command("dropDatabase")
    await mongo.close_database_connection()


async def override_get_redis_db() -> RedisDBManager:
    return redis


async def override_get_mongo_db() -> MongoDBManager:
    return mongo
