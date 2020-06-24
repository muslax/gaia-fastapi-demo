import logging
from typing import Dict, List

from bson.objectid import ObjectId
from pymongo import ReturnDocument

from app.api.utils import create_422_response
from app.core import config
from app.crud import utils
from app.db.mongo import AsyncIOMotorClient as DBClient
from app.models.company import CompanyBase, Contact

async def get(db: DBClient, ref: str):
    logging.info(f">>> {__name__}:{get.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_COMPANY)
    if ObjectId.is_valid(ref):
        return await utils.get(collection, ref)
    return await utils.get(collection, ref.upper(), "symbol")


async def get_multi(db: DBClient, limit: int, skip: int):
    logging.info(f">>> {__name__}:{get_multi.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_COMPANY)
    return await utils.get_multi(collection, limit, skip)


async def get_multi_by_filer(db: DBClient, filter: Dict, limit: int, skip: int):
    logging.info(f">>> {__name__}:{get_multi.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_COMPANY)
    # filter
    return await utils.get_multi_by_filter(collection, filter, limit, skip)


async def create(db: DBClient, data: CompanyBase):
    logging.info(f">>> {__name__}:{create.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_COMPANY)
    return await utils.create(collection, data)


async def update(db: DBClient, id: str, data: CompanyBase):
    logging.info(f">>> {__name__}:{update.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_COMPANY)
    return await utils.update(collection, id, data)

"""
Append tag to tags
> coll.update({'ref': ref}, {'$push': {'tags': new_tag}})
"""

async def add_contacts(db: DBClient, ref: str, data: List[Contact]):
    """sss"""
    logging.info(f">>> {__name__}:{add_contacts.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_COMPANY)
    modified_count = 0
    # Manually one by one
    # TODO:
    for x in data:
        rs = await collection.update_one(
            {"_id": ObjectId(ref)},
            {"$push": {"contacts": x.dict()}}
        )
        modified_count += rs.modified_count
    logging.info("Modified: " + str(modified_count))
    if rs.modified_count > 0:
        return data


async def remove_contact(db: DBClient, ref: str, contact: dict):
    """Remove contact"""
    logging.info(f">>> {__name__}:{remove_contact.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_COMPANY)

    return await collection.find_one_and_update(
        {"_id": ObjectId(ref)},
        {"$pull": {"contacts": contact}},
        {"_id": 0, "contacts": 1},
        return_document=ReturnDocument.AFTER
    )
