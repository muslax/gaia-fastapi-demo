import logging
from typing import Any, List

from bson.objectid import ObjectId
from fastapi.encoders import jsonable_encoder
from pymongo import ReturnDocument

from app.core.config import DOCTYPE_PERSONA
from app.core.security import get_password_hash, verify_password
from app.crud import utils
from app.db.mongo import AsyncIOMotorClient as DBClient
from app.models.persona import Battery, Persona, PersonaCreate, PersonaUpdate, Progress, ProjectPersona

# Persona always belongs to project
# Two personas in different projects can have identical username
#

async def authenticate(db: DBClient, username: str, password: str, prj_id: str):
    collection = utils.get_collection(db, DOCTYPE_PERSONA)
    user = await collection.find_one(
        {"username": username, "prj_id": ObjectId(prj_id)}
    )
    if not user:
        return None
    if not verify_password(password, user['hashed_password']):
        return None
    return user


async def authenticate_persona(db: DBClient, username: str, password: str, prj_id: str):
    logging.info(f">>> {__name__}:{authenticate_persona.__name__}")
    collection = utils.get_collection(db, DOCTYPE_PERSONA)
    user = await collection.find_one(
        {"username": username, "prj_id": ObjectId(prj_id)}
    )
    if not user:
        return None
    if not verify_password(password, user['hashed_password']):
        return None
    return user


async def update_progress(db: DBClient, prj_id: str, username: str, progress: Progress):
    collection = utils.get_collection(db, DOCTYPE_PERSONA)
    rs = await collection.find_one_and_update(
        {"prj_id": ObjectId(prj_id), "username": username},
        {"$set": {"progress": progress}},
        {"_id": 0, "progress": 1},
        return_document=ReturnDocument.AFTER
    )
    return rs



async def get(db: DBClient, ref: str):
    logging.info(f">>> {__name__}: {get.__name__}")
    collection = utils.get_collection(db, DOCTYPE_PERSONA)
    if ObjectId.is_valid(ref):
        return await utils.get(collection, ref)
    return await utils.get(collection, ref, "username")


async def get_multi(db: DBClient, limit: int, skip: int):
    logging.info(f">>> {__name__}:{get_multi.__name__}")
    collection = utils.get_collection(db, DOCTYPE_PERSONA)
    return await utils.get_multi(collection, limit, skip)


async def get_multi_filtered(db: DBClient, filter: dict, limit: int, skip: int):
    logging.info(f">>> {__name__}:{get_multi_filtered.__name__}")
    collection = utils.get_collection(db, DOCTYPE_PERSONA)
    return await utils.get_multi_by_filter(collection, filter, limit, skip)

# {
#     "fullname": "Lansia Sutopo",
#     "username": "lsutopo",
#     "email": "lsutopo@example.com",
#     "password": "lsutopo"
# }

async def create(db: DBClient, data: PersonaCreate):
    logging.info(f">>> {__name__}:{create.__name__}")
    collection = utils.get_collection(db, DOCTYPE_PERSONA)
    return await utils.create(collection, data)


# async def create_with_modules(db: DBClient, data: PersonaCreate, modules: List[str]):
#     logging.info(f">>> {__name__}:{create_with_modules.__name__}")


async def create_multi(db: DBClient, data: List[Any]):
    logging.info(f">>> {__name__}:{create_multi.__name__}")
    collection = utils.get_collection(db, DOCTYPE_PERSONA)
    # result = db.test.insert_many([{'x': i} for i in range(2)])
    # rs = await collection.insert_many([ {p.dict()} for p in data ])
    print(data)
    rs = await collection.insert_many(data)
    return rs.inserted_ids


async def update(db: DBClient, id: str, data: PersonaUpdate):
    logging.info(f">>> {__name__}:{update.__name__}")
    collection = utils.get_collection(db, DOCTYPE_PERSONA)
    return await utils.update(collection, id, data)


async def set_batteries(db: DBClient, id: str, batteries: List[Battery]):
    print(batteries)
    progress = Progress(
        state = "idle",
        battery = None,
        touched = None,
        next = batteries[0].type
    )
    collection = utils.get_collection(db, DOCTYPE_PERSONA)
    rs = await collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": {
            "batteries": jsonable_encoder(batteries),
            "progress": jsonable_encoder(progress)
        }},
        {"_id": 0, "batteries": 1},
        return_document=ReturnDocument.AFTER
    )
    return rs['batteries']


# CLASSROOM EVENTS
# ================


# async def set_status(db: DBClient, id: str, ts: int, mod: str, seq: int, finish: bool):
async def set_status(db: DBClient, id: str, ts: int, status: Progress):
    logging.info(f">>> {__name__}:{set_status.__name__}")
    collection = utils.get_collection(db, DOCTYPE_PERSONA)
    # return await utils.update(collection, id, data)
