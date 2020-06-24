import logging
from typing import List

from bson.objectid import ObjectId
from email_validator import validate_email

from app.core import config
from app.core.security import get_password_hash, verify_password
from app.crud import utils
from app.db.mongo import AsyncIOMotorClient as DBClient
from app.models.user import User, UserInApp, UserInDB, UserCreate, UserUpdate
from app.models.role import RoleEnum


async def authenticate(db: DBClient, username: str, password: str):
    logging.info(f">>> {__name__}:{authenticate.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_USER)
    user = await collection.find_one({"username": username, "type": "gaia",})
    if not user:
        return None
    if not verify_password(password, user['hashed_password']):
        return None
    return user


async def authenticate_licensee(
    db: DBClient,
    username: str,
    password: str,
    scope: str,
    context: str
    ):
    logging.info(f">>> {__name__}:{authenticate_licensee.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_USER)
    user = await collection.find_one(
        {"_id": ObjectId(context), "type": scope, "username": username}
    )
    if not user:
        return None
    if not verify_password(password, user['hashed_password']):
        return None
    return user


async def check_free_email_username(db: DBClient, username: str, email: str):
    logging.info(">>> " + __name__ + ":" + check_free_email_username.__name__ )
    collection = utils.get_collection(db, config.DOCTYPE_USER)
    user = await collection.find_one({"username": username})
    if user:
        return "Username already registered"
    user = await collection.find_one({"email": email})
    if user:
        return "Email already registered"


def is_active(user: UserInApp):
    return not user['disabled']


def is_superuser(user: UserInApp):
    return RoleEnum.superuser.value in utils.ensure_enums_to_strs(
        user['admin_roles'] or []
    )


def is_project_creator(user: UserInApp):
    return RoleEnum.projectcreator.value in utils.ensure_enums_to_strs(
        user['admin_roles'] or []
    )


def is_project_manager(user: UserInApp):
    return RoleEnum.projectmanager.value in utils.ensure_enums_to_strs(
        user['admin_roles'] or []
    )


def is_project_member(user: UserInApp):
    return RoleEnum.projectmember.value in utils.ensure_enums_to_strs(
        user['admin_roles'] or []
    )



# def is_project_lead(user: UserInDB):
#     return RoleEnum.projectlead.value in utils.ensure_enums_to_strs(
#         user['admin_roles'] or []
#     )


# def is_project_member(user: UserInDB):
#     return RoleEnum.projectmember.value in utils.ensure_enums_to_strs(
#         user['admin_roles'] or []
#     )


# def is_class_host(user: UserInDB):
#     return RoleEnum.classroomhost.value in utils.ensure_enums_to_strs(
#         user['admin_roles'] or []
#     )


async def get(db: DBClient, ref: str):
    logging.info(">>> " + __name__ + ":" + get.__name__ )
    collection = utils.get_collection(db, config.DOCTYPE_USER)
    if ObjectId.is_valid(ref):
        logging.info("objectid")
        return await utils.get(collection, ref)
    elif ("@" in ref) and ("." in ref):
        return await utils.get(collection, ref, "email")
    return await utils.get(collection, ref, "username")


async def get_multi(db: DBClient, limit: int = 50, skip: int = 0):
    logging.info(">>> " + __name__ + ":" + get_multi.__name__ )
    collection = utils.get_collection(db, config.DOCTYPE_USER)
    return await utils.get_multi(collection, limit, skip)


async def get_multi_by_filter(db: DBClient, limit: int = 50, skip: int = 0):
    logging.info(">>> " + __name__ + ":" + get_multi_by_filter.__name__ )
    collection = utils.get_collection(db, config.DOCTYPE_USER)
    return await utils.get_multi_by_filter(collection, filter, limit, skip)


async def create(db: DBClient, data: UserCreate):
    logging.info(">>> " + __name__ + ":" + create.__name__ )
    collection = utils.get_collection(db, config.DOCTYPE_USER)
    passwordhash = get_password_hash(data.password)
    user = UserInDB(**data.dict(), hashed_password=passwordhash)
    return await utils.create(collection, user)


async def create_many(db: DBClient, users: List[UserCreate]):
    logging.info(">>> " + __name__ + ":" + create_many.__name__ )
    collection = utils.get_collection(db, config.DOCTYPE_USER)
    data = []
    for x in users:
        dic = x.dict()
        dic["hashed_password"] = get_password_hash(x.password)
        print(dic)
        data.append(dic)
    rs = await collection.insert_many(data)
    ids = []
    for i in rs.inserted_ids:
        ids.append(str(i))
    return ids


# TODO not finished yet
async def update(db: DBClient, id:str, data: User):
    logging.info(">>> " + __name__ + ":" + create.__name__ )
    collection = utils.get_collection(db, config.DOCTYPE_USER)
    return await utils.update(collection, id=id, data=data)
