import logging
from typing import List

from bson.objectid import ObjectId
from email_validator import validate_email

from app.core import config
from app.core.security import get_password_hash, verify_password
from app.crud import utils
from app.db.mongo import AsyncIOMotorClient as DBClient
from app.models.user import User, UserBaseInDB, UserCreate, UserLogin, UserUpdate
# from app.utils import is_email


async def authenticate(db: DBClient, username: str, password: str):
    collection = utils.get_collection(db, config.USER_DOCTYPE)
    user = await collection.find_one({"username": username})
    if not user:
        return None
    if not verify_password(password, user['hashed_password']):
        return None
    return user


async def check_free_email_username(db: DBClient, data: UserLogin):
    logging.info(">>> " + __name__ + ":" + check_free_email_username.__name__ )
    collection = utils.get_collection(db, config.USER_DOCTYPE)
    user = await collection.find_one({"username": data.username})
    if user:
        return "Username already registered"
    user = await collection.find_one({"email": data.email})
    if user:
        return "Email already registered"


async def get(db: DBClient, ref: str):
    logging.info(">>> " + __name__ + ":" + get.__name__ )
    collection = utils.get_collection(db, config.USER_DOCTYPE)
    if ObjectId.is_valid(ref):
        logging.info("objectid")
        return await utils.get(collection, ref)
    elif ("@" in ref) and ("." in ref):
        return await utils.get(collection, ref, "email")
    return await utils.get(collection, ref, "username")


async def get_multi(db: DBClient, limit: int = 50, skip: int = 0):
    logging.info(">>> " + __name__ + ":" + get_multi.__name__ )
    collection = utils.get_collection(db, config.USER_DOCTYPE)
    return await utils.get_multi(collection, limit, skip)


async def create(db: DBClient, data: UserCreate):
    logging.info(">>> " + __name__ + ":" + create.__name__ )
    collection = utils.get_collection(db, config.USER_DOCTYPE)
    passwordhash = get_password_hash(data.password)
    user = UserBaseInDB(**data.dict(), hashed_password=passwordhash)
    return await utils.create(collection, user)


# TODO not finished yet
async def update(db: DBClient, id:str, data: User):
    logging.info(">>> " + __name__ + ":" + create.__name__ )
    collection = utils.get_collection(db, config.USER_DOCTYPE)
    return await utils.update(collection, id=id, data=data)
