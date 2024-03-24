"""Redis client class utility."""
import asyncio
import logging
from typing import Dict, Optional, Union

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession
from pymongo import results
from pymongo.database import Database

from app.api.utils import exception_utils
from app.core.mongo_config import MongoConfig


class ZuMongoClient(object):

    mongo_client: AsyncIOMotorClient = None
    databases: Dict[str, Database] = {}
    log: logging.Logger = logging.getLogger(__name__)

    @classmethod
    async def open_mongo_client(cls):
        if cls.mongo_client is None:
            cls.mongo_client = AsyncIOMotorClient(MongoConfig.MONGODB_URL)
            cls.mongo_client.get_io_loop = asyncio.get_running_loop
        return cls.mongo_client

    @classmethod
    async def close_mongo_client(cls):
        if cls.mongo_client:
            cls.log.debug("Closing Mongo client")
            cls.databases = {}
            cls.mongo_client.close()

    @classmethod
    async def open_database(cls, dbname: str):
        if cls.databases.get(dbname) is None:
            cls.databases[dbname] = cls.mongo_client[dbname]

    @classmethod
    async def close_database(cls, dbname: str):
        if cls.databases.get(dbname):
            del cls.databases[dbname]

    @classmethod
    def __check_if_database_present(cls, db: str):
        # sourcery skip: raise-specific-error
        if cls.databases.get(db) is None:
            raise Exception("Check database name or create db connection")

    @classmethod
    async def find_one(
        cls,
        col: str,
        filter_data: Dict,
        project: Dict = None,
        db: str = MongoConfig.MONGO_PROD_DATABASE,
        session: AsyncIOMotorClientSession = None,
        **kwargs
    ) -> Union[Dict, None]:
        if project is None:
            project = {}
        cls.__check_if_database_present(db)
        try:
            return await cls.databases[db][col].find_one(
                filter=filter_data, projection=project, session=session, **kwargs
            )
        except Exception as e:
            print(e)
            if session:
                session.abort_transaction()
            exception_utils.log_and_raise_exception(
                "Unexpected exception", str(e), "Internal Server Error"
            )

    @classmethod
    def find(
        cls,
        col: str,
        filter_data: Dict,
        project: Dict = None,
        db: str = MongoConfig.MONGO_PROD_DATABASE,
        session: AsyncIOMotorClientSession = None,
        **kwargs
    ):
        if project is None:
            project = {}
        cls.__check_if_database_present(db)
        try:
            return cls.databases[db][col].find(
                filter=filter_data, projection=project, session=session, **kwargs
            )
        except Exception as e:
            if session:
                session.abort_transaction()
            exception_utils.log_and_raise_exception(
                "Unexpected exception", str(e), "Internal Server Error"
            )

    @classmethod
    async def insert_one(
        cls,
        col: str,
        insert_data: Dict,
        db: str = MongoConfig.MONGO_PROD_DATABASE,
        session: AsyncIOMotorClientSession = None,
        **kwargs
    ) -> results.InsertOneResult:
        cls.__check_if_database_present(db)
        try:
            return await cls.databases[db][col].insert_one(
                document=insert_data, session=session, **kwargs
            )
        except Exception as e:
            if session:
                session.abort_transaction()
            exception_utils.log_and_raise_exception(
                "Unexpected exception", str(e), "Internal Server Error"
            )

    @classmethod
    async def delete_one(
        cls,
        col: str,
        filter_data: Dict,
        db: str = MongoConfig.MONGO_PROD_DATABASE,
        session: AsyncIOMotorClientSession = None,
        **kwargs
    ) -> results.DeleteResult:
        cls.__check_if_database_present(db)
        try:
            return await cls.databases[db][col].delete_one(
                filter=filter_data, session=session, **kwargs
            )
        except Exception as e:
            if session:
                session.abort_transaction()
            exception_utils.log_and_raise_exception(
                "Unexpected exception", str(e), "Internal Server Error"
            )

    @classmethod
    async def update_one(
        cls,
        col: str,
        filter_data: Dict,
        update_data: Dict = None,
        upsert=False,
        db: str = MongoConfig.MONGO_PROD_DATABASE,
        session: AsyncIOMotorClientSession = None,
        **kwargs
    ) -> Optional[results.UpdateResult]:
        if update_data is None:
            update_data = {}
        cls.__check_if_database_present(db)
        try:
            return await cls.databases[db][col].update_one(
                filter=filter_data,
                update=update_data,
                upsert=upsert,
                session=session,
                **kwargs
            )
        except Exception as e:
            if session:
                session.abort_transaction()
            exception_utils.log_and_raise_exception(
                "Unexpected exception", str(e), "Internal Server Error"
            )

    @classmethod
    async def update_many(
        cls,
        col: str,
        filter_data: Dict,
        update_data: Dict = None,
        upsert=False,
        db: str = MongoConfig.MONGO_PROD_DATABASE,
        session: AsyncIOMotorClientSession = None,
        **kwargs
    ) -> Optional[results.UpdateResult]:
        if update_data is None:
            update_data = {}
        cls.__check_if_database_present(db)
        try:
            return await cls.databases[db][col].update_many(
                filter=filter_data,
                update=update_data,
                upsert=upsert,
                session=session,
                **kwargs
            )
        except Exception as e:
            if session:
                session.abort_transaction()
            exception_utils.log_and_raise_exception(
                "Unexpected exception", str(e), "Internal Server Error"
            )

    @classmethod
    async def call_func(
        cls,
        func: str,
        db: str,
        col: str,
        session: AsyncIOMotorClientSession = None,
        **kwargs
    ):
        cls.__check_if_database_present(db)
        try:
            return await getattr(cls.databases[db][col], func)(
                session=session, **kwargs
            )
        except Exception as e:
            if session:
                session.abort_transaction()
            exception_utils.log_and_raise_exception(
                "Unexpected exception", str(e), "Internal Server Error"
            )
