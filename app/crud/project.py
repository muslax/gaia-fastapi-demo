import logging
from typing import Dict, List

from fastapi import HTTPException
from bson.objectid import ObjectId
from pymongo import ReturnDocument

from app.api.utils import create_422_response, create_aliased_response
from app.core import config
from app.core.security import get_password_hash, verify_password
from app.crud import utils
from app.db.mongo import AsyncIOMotorClient as DBClient
from app.models.base import Workbook
from app.models.batch import (Batch, BatchBase, BatchCreate, FacetimeSession,
                              WorkbookSession)
from app.models.project import (Guest, GuestCreate, ProjectBase,
                                ProjectCreate, ProjectInDB)
from app.models.persona import Battery
from app.models.user import UserInApp, UserInDB

# TODO fix
# async def check_contact(username: str, id: str):
#     logging.info(f">>> {__name__}:{check_contact.__name__}")
#     collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
#     # https://stackoverflow.com/questions/10610131/checking-if-a-field-contains-a-string
#     return await collection.find_one(
#         {"_id": ObjectId(id), "username": {"$regex": username}}
#     )

# TODO fix
# async def check_expert(username: str, id: str):
#     pass

async def get_project_member(db: DBClient, prj_id: str, username: str):
    logging.info(f">>> {__name__}:{get_project_member.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    rs = await collection.find_one(
        {"_id": ObjectId(prj_id), "members.username": username},
        {
            "_id": 0,
            "members": {"$elemMatch": {"username": username}}
        }
    )
    if len(rs['members']) > 0:
        user = rs['members'][0]
        # user['type'] = user['role']
        return user
    return None


async def authenticate_member(db: DBClient, username: str, password: str,
role: str, context: str):
    logging.info(f">>> {__name__}:{authenticate_member.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    rs = await collection.find_one(
        {"_id": ObjectId(context), "members.username": username},
        {"_id": 0,
            "members": {"$elemMatch": {"username": username, "type": role}}}
    )
    if not rs:
        return None
    if len(rs['members']) > 0:
        user = rs['members'][0]
        # print(user)
        if verify_password(password, user['hashed_password']):
            return user


async def is_project_manager(db: DBClient, user: UserInApp, id: str):
    logging.info(f">>> {__name__}:{is_project_manager.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    rs = await collection.find_one(
        {'_id': ObjectId(id), 'lead_by': user['username']},
        {'_id': 0, 'lead_by': 1}
    )
    if rs is None:
        return False
    return user['username'] == rs['lead_by']


async def is_project_member(db: DBClient, user: UserInApp, id: str):
    logging.info(f">>> {__name__}:{is_project_member.__name__}")
    if await is_project_manager(db, user, id):
        return True
    return user['context'] == id;


async def get(db: DBClient, id: str):
    logging.info(f">>> {__name__}:{get.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    return await utils.get(collection, id)


async def get_multi(db: DBClient, limit: int, skip: int):
    logging.info(f">>> {__name__}:{get_multi.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    return await utils.get_multi(collection, limit, skip)


async def get_multi_by_filter(db: DBClient, filter: dict, limit: int = 50, skip: int = 0):
    logging.info(">>> " + __name__ + ":" + get_multi_by_filter.__name__ )
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    # filter = {}
    return await utils.get_multi_by_filter(collection, filter, limit, skip)


async def get_project_manager(db: DBClient, id: str):
    logging.info(f">>> {__name__}:{get_project_manager.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    rs = await collection.find_one(
        {'_id': ObjectId(id)},
        {'_id': 0, 'lead_by': 1}
    )
    print(rs)
    return rs['lead_by']


async def create(db: DBClient, data: ProjectCreate):
    logging.info(f">>> {__name__}:{create.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    data = ProjectInDB(**data.dict())
    return await utils.create(collection, data)


async def update(db: DBClient, id: str, data: ProjectBase):
    logging.info(f">>> {__name__}:{update.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    return await utils.update(collection, id, data)


async def check_free_member_slot(db: DBClient, id: str, email: str,
username: str):
    logging.info(f">>> {__name__}:{check_free_member_slot.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    rs = await collection.find_one(
        {
            "_id": ObjectId(id),
            "$or": [{"members.username": username}, {"members.email": email}]
        },
        {"_id": 0, "members": 1}
    )
    return rs is None


async def add_member(db: DBClient, ref: str, mtype: str, data: GuestCreate):
    logging.info(f">>> {__name__}:{add_member.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)

    dic = {
        "_id": str(ObjectId()),
        **data.dict(),
        "type": mtype,
        "hashed_password": get_password_hash(data.password)
    }
    del dic["password"]
    rs = await collection.find_one_and_update(
        {"_id": ObjectId(ref)},
        {"$push": {"members": dic}},
        {"_id": 0, "members": {"$elemMatch": {"username": data.username}}},
        return_document=ReturnDocument.AFTER
    )
    if rs['members']:
        return rs['members'][0]
    return None


async def get_members(db: DBClient, id: str, type: str):
    logging.info(f">>> {__name__}:{get_members.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    rs = await collection.find_one(
        {"_id": ObjectId(id)},
        {"_id": 0, "members": 1}
    )
    members = rs['members']
    guests = []
    for guest in members:
        if guest['type'] == type:
            guests.append(Guest(**guest))
    return guests


async def get_batches(db: DBClient, id: str):
    logging.info(f">>> {__name__}:{get_members.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    rs = await collection.find_one(
        {"_id": ObjectId(id)},
        {"_id": 0, "batches": 1}
    )
    batches = rs['batches']
    print(batches)
    return batches


async def create_batch(db: DBClient, id: str, data: BatchCreate):
    logging.info(f">>> {__name__}:{create_batch.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    batch_id = str(ObjectId())
    batch = Batch(
        batch_id = batch_id,
        **data.dict()
    )
    rs = await collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$push": {"batches": batch.dict()}},
        {"_id": 0, "batches": {"$elemMatch": {"batch_id": batch_id}}},
        return_document=ReturnDocument.AFTER
    )
    print(rs)
    return rs['batches'][0]

# user = UserInDB(**data.dict(), hashed_password=passwordhash)
# return await utils.create(collection, user)

async def add_workbook_session(db: DBClient, id: str, batch_id: str,
data: WorkbookSession):
    logging.info(f">>> {__name__}:{add_workbook_session.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    dic = data.dict()

    """batches.$.workbook_sessions => matched index"""
    rs = await collection.find_one_and_update(
        {"_id": ObjectId(id), "batches.batch_id": batch_id},
        {"$push": {"batches.$.workbook_sessions": dic}},
        {"_id": 0, "batches": {"$elemMatch": {"batch_id": batch_id}}},
        return_document=ReturnDocument.AFTER
    )
    print(rs)
    count = len(rs['batches'][0]['workbook_sessions'])
    return rs['batches'][0]['workbook_sessions'][count -1]


async def add_facetime_session(db: DBClient, id: str, batch_id: str,
data: FacetimeSession):
    logging.info(f">>> {__name__}:{add_facetime_session.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    # dic = data.dict()
    """
    $ matched index
    """
    rs = await collection.find_one_and_update(
        {"_id": ObjectId(id), "batches.batch_id": batch_id},
        {"$push": {"batches.$.facetime_sessions": data.dict()}},
        {"_id": 0, "batches": {"$elemMatch": {"batch_id": batch_id}}},
        return_document=ReturnDocument.AFTER
    )
    print(rs)
    count = len(rs['batches'][0]['facetime_sessions'])
    return rs['batches'][0]['facetime_sessions'][count -1]

# workbook_sessions
# workbook_sessions:

async def _create_batch(db: DBClient, id: str, participants: List[str]):
    logging.info(f">>> {__name__}:{add_batch.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    bid = str(ObjectId())
    print(participants)
    batch = {
        "_id": bid,
        "participants": participants
    }
    rs = await collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$push": {"batches": batch}},
        {"_id": 0, "batches": {"$elemMatch": {"_id": bid}}},
        return_document=ReturnDocument.AFTER
    )
    return rs['batches'][0]


async def add_batch(db: DBClient, id: str, data: BatchBase):
    logging.info(f">>> {__name__}:{add_batch.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    bid = str(ObjectId())
    batch = {
        "_id": bid,
        **data.dict()
    }
    rs = await collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$push": {"batches": batch}},
        {"_id": 0, "batches": {"$elemMatch": {"_id": bid}}},
        return_document=ReturnDocument.AFTER
    )
    print("----------------")
    print(rs)
    print(rs['batches'][0])
    return rs['batches'][0]


async def add_note(db: DBClient, prj_id: str, note: str):
    logging.info(f">>> {__name__}:{add_note.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    rs = await collection.find_one_and_update(
        {"_id": ObjectId(prj_id)},
        {"$push": {"notes": note}},
        {"_id": 0, "notes": [note]},
        return_document=ReturnDocument.AFTER
    )
    print(rs['notes'][0])
    return rs['notes'][0]


"""async def add_members(db: DBClient, ref: str, mtype: str,
data: List[ProjectContactCreate]):
    logging.info(f">>> {__name__}:{add_members.__name__}")

    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)

    result = []
    for x in data:
        newid = ObjectId()
        dic = {
            "_id": newid,
            **x.dict(),
            "role": mtype,
            "hashed_password": get_password_hash(x.password)
        }
        del dic["password"]
        rs = await collection.update_one(
            {"_id": ObjectId(ref)},
            {"$push": {"members": dic}},
            # {"_id": 0,
            #  "members": {
            #      "$elemMatch": {"username": x.username, "role": mtype}}}
        )
        result.append(str(newid))
    return (result)"""


async def add_clients(db: DBClient, ref: str, data: List[GuestCreate]):
    """sss"""
    logging.info(f">>> {__name__}:{add_clients.__name__}")

    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    modified_count = 0
    # Manually one by one
    # TODO:
    for x in data:
        dic = x.dict()
        dic["role"] = "client"
        dic["hashed_password"] = get_password_hash(x.password)
        del dic["password"]
        rs = await collection.update_one(
            {"_id": ObjectId(ref)},
            {"$push": {"members": dic}}
        )
        modified_count += rs.modified_count
    logging.info("Modified: " + str(modified_count))
    if rs.modified_count > 0:
        return data


async def _add_batch(db: DBClient, id: str, data: BatchBase):
    logging.info(f">>> {__name__}:{add_batch.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    dic = {
        "_id": str(ObjectId()),
        **data.dict()
    }
    # dic = data.dict()
    # dic['_id'] = str(ObjectId())
    print(dic)
    rs = await collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$push": {"batches": dic}},
        {"_id": 0, "batches": [dic]},
        return_document=ReturnDocument.AFTER
    )
    print(rs['batches'][0])
    return rs['batches'][0]


async def add_module(db: DBClient, id: str, data: Workbook,
facetime: bool=False):
    """Add one or more modules"""
    logging.info(f">>> {__name__}:{add_module.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    group = "workbooks"
    if facetime:
        group = "facetimes"
    rs = await collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$push": {group: data.dict()}},
        {"_id": 0, group: {"$elemMatch": {"type": data.type}}},
        return_document=ReturnDocument.AFTER
    )
    print(rs)
    return rs[group][0]


async def edit_workbook(db: DBClient, id: str, type: str, info: dict):
    logging.info(f">>> {__name__}:{edit_workbook.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    rs = await collection.find_one_and_update(
        {"_id": ObjectId(id), "workbooks.type": type},
        {"$set": {"workbooks.$": info}},
        {"_id": 0, "workbooks": {"$elemMatch": {"type": type}}},
        return_document=ReturnDocument.AFTER
    )
    if rs is None:
        return None
    elif (rs['workbooks'] is None or len(rs['workbooks']) == 0):
        return None
    return rs['workbooks'][0]


async def delete_workbook(db: DBClient, id: str, type: str):
    logging.info(f">>> {__name__}:{delete_workbook.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    rs = await collection.find_one_and_update(
        {"_id": ObjectId(id), "workbooks.type": type},
        {"$pull": {"workbooks": {"type": type}}},
        {"_id": 0, "workbooks": 1},
        return_document=ReturnDocument.AFTER
    )
    if not rs == None:
        return rs['workbooks']
    return None


async def edit_facetime(db: DBClient, id: str, type: str, info: dict):
    logging.info(f">>> {__name__}:{edit_facetime.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    rs = await collection.find_one_and_update(
        {"_id": ObjectId(id), "facetimes.type": type},
        {"$set": {"facetimes.$": info}},
        {"_id": 0, "facetimes": {"$elemMatch": {"type": type}}},
        return_document=ReturnDocument.AFTER
    )
    if rs is None:
        return None
    elif (rs['facetimes'] is None or len(rs['facetimes']) == 0):
        return None
    return rs['facetimes'][0]


async def delete_facetime(db: DBClient, id: str, type: str):
    logging.info(f">>> {__name__}:{delete_facetime.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    rs = await collection.find_one_and_update(
        {"_id": ObjectId(id), "facetimes.type": type},
        {"$pull": {"facetimes": {"type": type}}},
        {"_id": 0, "facetimes": 1},
        return_document=ReturnDocument.AFTER
    )
    if not rs == None:
        return rs['facetimes']
    return None


async def get_modules(db: DBClient, id: str, type: str=""):
    logging.info(f">>> {__name__}:{add_module.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    # group = "workbooks"
    rs = await collection.find_one(
        {"_id": ObjectId(id)},
        {"_id": 0, "workbooks": 1, "facetimes": 1}
    )
    workbooks = rs['workbooks']
    facetimes = rs['facetimes']
    modules = workbooks + facetimes
    if type == "workbook":
        return workbooks
    elif type == "facetime":
        return facetimes
    return modules


async def add_modules(db: DBClient, ref: str, data: List[Workbook]):
    """Add one or more modules"""
    logging.info(f">>> {__name__}:{add_modules.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    modified_count = 0
    # Manually one by one
    # TODO:
    for x in data:
        rs = await collection.update_one(
            {"_id": ObjectId(ref)},
            {"$push": {"modules": x.dict()}}
        )
        modified_count += rs.modified_count
    logging.info("Modified: " + str(modified_count))
    if rs.modified_count > 0:
        return data


async def batch_batteries(db: DBClient, id: str, batch_id: str):
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    rs = await collection.find_one(
        {"_id": ObjectId(id)},
        {"_id": 0, "batches": {"$elemMatch": {"batch_id": batch_id}}}
    )
    batch = rs['batches'][0]
    sessions = batch['workbook_sessions'] + batch['facetime_sessions']
    batteries: List[Battery] = []
    for a in sessions:
        batteries.append(Battery(
            type = a['module'],
            items = a['module_items'],
            touched = 0
        ))
    return batteries


async def prepare_persona_batteries(db: DBClient, id: str, batch_id: str):
    """Update batch participants' progress and batteries"""
    logging.info(f">>> {__name__}:{prepare_persona_batteries.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    rs = await collection.find_one(
        {"_id": ObjectId(id), "batches.batch_id": batch_id},
        {
            "_id": 0,
            "workbooks": 1,
            "facetimes": 1,
            "batches": {"$elemMatch": {"batch_id": batch_id}}
        }
    )

    batch = rs['batches'][0]
    usernames = batch['participants']
    sessions = batch['workbook_sessions'] + batch['facetime_sessions']
    batteries = []
    for a in sessions:
        batteries.append({
            'type': a['module'],
            'items': a['module_items'],
            'touched': None
        })
    progress = {
        'state': "idle",
        'battery': None,
        'touched': None,
        'next': batteries[0]['type']
    }

    collection = utils.get_collection(db, config.DOCTYPE_PERSONA)
    rs = await collection.update_many(
        {"prj_id": ObjectId(id), "username": {"$in": usernames}},
        {"$set": {
            "batteries": batteries,
            "progress": progress
        }}
    )
    return {"updated_personas": rs.modified_count}


async def prepare_persona_evidences(db: DBClient, id: str, batch_id: str):
    logging.info(f">>> {__name__}:{prepare_persona_evidences.__name__}")
    collection = utils.get_collection(db, config.DOCTYPE_PROJECT)
    rs = await collection.find_one(
        {"_id": ObjectId(id), "batches.batch_id": batch_id},
        {
            "_id": 0,
            "batches": {"$elemMatch": {"batch_id": batch_id}}
        }
    )
    batch = rs['batches'][0]
    usernames = batch['participants']
    sessions = batch['workbook_sessions'] + batch['facetime_sessions']

    # Collect workbook type and
    batteries = []
    for a in sessions:
        batteries.append({
            'type': a['module'],
            'items': a['module_items']
        })
