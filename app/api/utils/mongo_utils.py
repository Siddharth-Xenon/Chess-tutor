import logging

from fastapi.exceptions import HTTPException
from pymongo import collection as cltn
from pymongo import errors, results
from starlette.status import HTTP_409_CONFLICT

from app.api.utils import exception_utils

logger = logging.getLogger(__name__)


async def find_one(
    collection: cltn.Collection, filter_data, request_id: str, get_cols=None
):
    try:
        if get_cols:
            value = await collection.find_one(filter_data, get_cols)
        else:
            value = await collection.find_one(filter_data)
        return value
    except Exception as e:
        exception_utils.log_and_raise_exception(
            "Unexpected exception", request_id, str(e), "Internal Server Error"
        )


async def find(collection: cltn.Collection, filter_data, request_id: str):
    try:
        res = []
        async for value in collection.find(filter_data):
            res.append(value)
        return res
    except Exception as e:
        exception_utils.log_and_raise_exception(
            "Unexpected exception", request_id, str(e), "Internal Server Error"
        )


async def insert_one(collection: cltn.Collection, insert_data, request_id: str):
    try:
        value = await collection.insert_one(insert_data)
        return value
    except errors.DuplicateKeyError:
        raise HTTPException(HTTP_409_CONFLICT, "duplicate key")
    except Exception as e:
        exception_utils.log_and_raise_exception(
            "Unexpected exception", request_id, str(e), "Internal Server Error"
        )


async def delete_one(collection: cltn.Collection, filter_data, request_id: str):
    try:
        value = await collection.delete_one(filter_data)
        return value
    except Exception as e:
        exception_utils.log_and_raise_exception(
            "Unexpected exception", request_id, str(e), "Internal Server Error"
        )


async def delete_many(collection: cltn.Collection, filter_data, request_id: str):
    try:
        value = await collection.delete_many(filter_data)
        return value
    except Exception as e:
        exception_utils.log_and_raise_exception(
            "Unexpected exception", request_id, str(e), "Internal Server Error"
        )


async def update_one(
    collection: cltn.Collection,
    filter_data,
    update_data,
    request_id: str,
    upsert: bool = False,
) -> results.UpdateResult:
    try:
        value = await collection.update_one(
            filter=filter_data, update=update_data, upsert=upsert
        )
        return value
    except Exception as e:
        exception_utils.log_and_raise_exception(
            "Unexpected exception", request_id, str(e), "Internal Server Error"
        )
