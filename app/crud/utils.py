import logging
from enum import Enum
from typing import Dict, List, Optional, Sequence, Type, TypeVar, Union

from pydantic import BaseModel
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection as Collection
from pymongo import ReturnDocument

from app.db.mongo import AsyncIOMotorClient
from app.core.config import MONGODB_NAME



def get_collection(db: AsyncIOMotorClient, doc_type: str):
    return db[MONGODB_NAME][doc_type]


def ensure_enums_to_strs(items: Union[Sequence[Union[Enum, str]], Type[Enum]]):
    str_items = []
    for item in items:
        if isinstance(item, Enum):
            str_items.append(str(item.value))
        else:
            str_items.append(str(item))
    return str_items


async def get(collection: Collection, seek: str, field="_id"):
    logging.info(">>> " + __name__ + ":" + get.__name__ )
    if field == "_id":
        return await collection.find_one({"_id": ObjectId(seek)})
    else:
        return await collection.find_one({field: seek})


async def get_by_dict(collection: Collection, fields: dict):
    """Example: get_by_dict(collection, {"username": "agus"}) """
    logging.info(">>> " + __name__ + ":" + get_by_dict.__name__ )
    return await collection.find_one(fields)


async def get_multi(collection: Collection, limit: int = 20, skip: int = 0):
    logging.info(">>> " + __name__ + ":" + get_multi.__name__ )
    rs: List[BaseModel] = []
    cursor = collection.find({}, limit=limit, skip=skip)
    async for row in cursor:
        rs.append(row)
    return rs


async def get_multi_by_filter(
    collection: Collection, filter: Dict, limit: int = 20, skip: int = 0
    ):
    """Example: filter = { "phone": "123" }"""
    logging.info(">>> " + __name__ + ":" + get_multi_by_filter.__name__ )
    rs: List[BaseModel] = []
    cursor = collection.find(filter=filter, limit=limit, skip=skip)
    async for row in cursor:
        rs.append(row)
    return rs


async def create(collection: Collection, data: BaseModel):
    logging.info(">>> " + __name__ + ":" + create.__name__ )
    _dict = data.dict()
    try:
        logging.info("Trying to insert new document...")
        rs = await collection.insert_one(_dict)
        if rs.inserted_id:
            return await collection.find_one({"_id": rs.inserted_id})
    except Exception as e:
        logging.error("Failed: " + str(e))
    return None


async def update(collection: Collection, id: str, data: BaseModel):
    logging.info(">>> " + __name__ + ":" + update.__name__ )
    found = await collection.find_one({"_id": ObjectId(id)}, {"_id": 1})
    if found:
        _dict = data.dict()
        excludes = []  # TODO
        for k in _dict:
            if not _dict[k]:
                excludes.append(k)
        print(excludes)
        for i in excludes:
            del _dict[i]

        # rs = await collection.update_one(
        #         {"_id": ObjectId(id)},
        #         {"$set": _dict}
        #     )
        # if rs.modified_count:
        #     return await collection.find_one({"_id": ObjectId(id)})
        return await collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": _dict},
            return_document=ReturnDocument.AFTER
        )
    return None


async def delete(collection: Collection, id: str):
    deleted = await collection.find_one_and_delete({"_id": ObjectId(id)})
    if deleted:
        return deleted
    return None

