import logging
from random import shuffle
from time import time
from typing import List

from bson.objectid import ObjectId
from pymongo import ReturnDocument

# from app.m
from app.core.config import DOCTYPE_EV_GPQ, DOCTYPE_PERSONA, GPQ_TOTAL_ITEMS
from app.crud import utils as crudutils
from app.db.mongo import AsyncIOMotorClient as DBClient
from app.models.dbmodel import BaseModel
from app.models.pev.gpq import GPQEvidenceInDB, GPQRow


gpq_touch_stacks = {}


async def get_multi(db: DBClient, limit: int, skip: int):
    logging.info(f">>> {__name__}:{get_multi.__name__}")
    collection = crudutils.get_collection(db, DOCTYPE_EV_GPQ)
    return await crudutils.get_multi(collection, limit, skip)


async def get_by_project(db: DBClient, id: str, limit: int, skip: int):
    logging.info(f">>> {__name__}:{get_by_project.__name__}")
    collection = crudutils.get_collection(db, DOCTYPE_EV_GPQ)
    rs: List[BaseModel] = []
    cursor = collection.find(
        {"prj_id": ObjectId(id)},
        limit=limit,
        skip=skip
    )
    async for row in cursor:
        rs.append(row)
    return rs


async def create_template(
    db: DBClient, prj_id: str, username: str, fullname: str, rows: int
    ):
    logging.info(f">>> {__name__}:{create_template.__name__}")
    records: List[GPQRow] = []
    seqs = [i for i in range(1, rows + 1)]
    shuffle(seqs)

    for i in range(rows):
        records.append(GPQRow(
            seq = i + 1,
            wb_seq = seqs[i]
        ))

    collection = crudutils.get_collection(db, DOCTYPE_EV_GPQ)
    template = {
        'prj_id': ObjectId(prj_id),
        'username': username,
        'fullname': fullname,
        'records': records
    }
    data = GPQEvidenceInDB(**template)
    return await crudutils.create(collection, data)


# > if it is in stacks:
#     > just return
# > if not: check db
#     > if not in db (hot init)
#         > just create one in stacks
#         > save to db
#     > if it is in db, it may be app has restarted or user has logout before
#         > retrieve from db
#         > copy to stacks
#         > update `touched`

async def init(db: DBClient, id: str):
    logging.info(f">>> {__name__}:{init.__name__}")

    # If it is in stacks, just return it
    if (id in gpq_touch_stacks and
        "initiated" in gpq_touch_stacks[id] and
        gpq_touch_stacks[id]["initiated"]):
        return { "initiated": gpq_touch_stacks[id]["initiated"] }
    # It is not in stacks, check db
    else:
        gpq_touch_stacks[id] = {
            "initiated": None, "started": None, "touched": None
        }
        # Check state from db
        collection = crudutils.get_collection(db, DOCTYPE_EV_GPQ)
        ev = await collection.find_one(
            {"_id": ObjectId(id)},
            {"_id": 0, "initiated": 1, "started": 1}
        )
        logging.info( str(ev) )

        ts = round(time() * 1000)
        if not ev["initiated"] or ev["initiated"] is None:
            gpq_touch_stacks[id]["initiated"] = ts
            gpq_touch_stacks[id]["started"] = None
            gpq_touch_stacks[id]["touched"] = ts
            rs = await collection.find_one_and_update(
                { "_id": ObjectId(id) },
                { "$set": { "initiated": ts, "touched": ts } },
                {"_id": 0, "initiated": 1},
                return_document=ReturnDocument.AFTER
            )
            return rs
        else:
            gpq_touch_stacks[id]["initiated"] = ev["initiated"]
            if ev["started"]:
                gpq_touch_stacks[id]["started"] = ev["started"]
            gpq_touch_stacks[id]["touched"] = ts
            rs = await collection.find_one_and_update(
                { "_id": ObjectId(id) },
                { "$set": { "touched": ts } },
                {"_id": 0, "initiated": 1}
            )
            return rs


async def start(db: DBClient, id: str):
    logging.info(f">>> {__name__}:{start.__name__}")
    collection = crudutils.get_collection(db, DOCTYPE_EV_GPQ)
    ts = round(time() * 1000)
    gpq_touch_stacks[id] = ts
    print(gpq_touch_stacks)
    rs = await collection.find_one_and_update(
        { "_id": ObjectId(id) },
        { "$set": { "started": ts, "touched": ts } },
        { "_id": 0, u"started": 1 },
        return_document=ReturnDocument.AFTER
    )
    return rs


async def update(
    db: DBClient,
    id: str,
    seq: int,
    wb_seq: int,
    element: str,
    statement: str,
    # last_touch: int
    ):
    logging.info(f">>> {__name__}:{update_row.__name__}")
    collection = crudutils.get_collection(db, DOCTYPE_EV_GPQ)

    if not id in gpq_touch_stacks:
        # If app has been restarted and id isn't in stack
        ev = await collection.find_one({ "_id": ObjectId(id) }, { "_id": 1, "touched": 1 })
        gpq_touch_stacks[id] = ev["touched"]

    last_touch = gpq_touch_stacks[id]
    ts = round(time() * 1000)
    elapsed = ts - last_touch
    gpq_touch_stacks[id] = ts

    dic = {}
    dic['seq'] = seq
    dic['wb_seq'] = wb_seq
    dic['element'] = element
    dic['statement'] = statement

    dic["saved"] = ts
    dic["elapsed"] = elapsed
    index = seq - 1
    docpath = "records." + str(index)

    rs = await collection.find_one_and_update(
        { "_id": ObjectId(id) },
        { "$set": { "touched": ts, docpath: dic } },
        { "_id": 0, u"touched": 1 },
        return_document=ReturnDocument.AFTER
    )
    if rs:
        return rs  # ['records'][index]
    return None









async def create_db_template(
    db: DBClient,
    prj_id: str,
    username: str,
    fullname: str,
    rows: int = GPQ_TOTAL_ITEMS
):
    """
    We just persist data. Make sure you provide correct
    `prj_id`, `username`, and `fullname`.
    """
    logging.info(f">>> {__name__}:{create_db_template.__name__}")
    # if not ObjectId.is_valid(prj_id):
    #     return None

    prj_id = ObjectId(prj_id)
    records: List[GPQRow] = []
    seqs = [i for i in range(1, rows + 1)]
    shuffle(seqs)

    for i in range(rows):
        records.append(GPQRow(
            seq = i + 1,
            wb_seq = seqs[i]
        ))
    collection = crudutils.get_collection(db, DOCTYPE_EV_GPQ)
    template = {
        'prj_id': prj_id,
        'username': username,
        'fullname': fullname,
        'records': records
    }
    data = GPQEvidenceInDB(**template)
    return await crudutils.create(collection, data)


async def create_db_template2(
    db: DBClient,
    prj_id: str,
    # username: str,
    # fullname: str,
    persona_id: str,
    rows: int = GPQ_TOTAL_ITEMS
):
    logging.info(f">>> {__name__}:{create_db_template.__name__}")
    # if not ObjectId.is_valid(prj_id):
    #     return None

    collection = crudutils.get_collection(db, DOCTYPE_PERSONA)
    persona = await collection.find_one({"_id": ObjectId(persona_id)})
    print(persona)
    print("----------------------")
    # return {"response": "test"}

    _id = "GPQ" + persona_id
    prj_id = ObjectId(prj_id)
    records: List[GPQRow] = []
    seqs = [i for i in range(1, rows + 1)]
    shuffle(seqs)

    for i in range(rows):
        records.append(GPQRow(
            seq = i + 1,
            wb_seq = seqs[i]
        ))
    collection = crudutils.get_collection(db, DOCTYPE_EV_GPQ)
    template = {
        '_id': _id,
        'prj_id': prj_id,
        'username': persona['username'],
        'fullname': persona['fullname'],
        'records': records
    }
    print(template)
    data = GPQEvidenceInDB(**template)
    return await crudutils.create(collection, data)


"""
- init      -1
- start     0
- update    n
- finish    null

"""

async def init2(db: DBClient, id: str):
    logging.info(f">>> {__name__}:{init.__name__}")
    collection = crudutils.get_collection(db, DOCTYPE_EV_GPQ)
    ts = round(time() * 1000)
    rs = await collection.find_one_and_update(
        { "_id": ObjectId(id) },
        { "$set": { "started": ts, "touched": ts } },
        { "_id": 0, u"started": 1 },
        return_document=ReturnDocument.AFTER
    )
    return rs


"""
{
  "seq": 6,
  "wb_seq": 105,
  "element": "ATK",
  "statement": "Menebak arti dari 5e8795eb1f0bc0ead3ae1fb0",
  "saved": 1585948296263, # python generated
  "elapsed": 67800
}
"""

async def update_row(db: DBClient, id: str, data: GPQRow):
    logging.info(f">>> {__name__}:{update_row.__name__}")
    collection = crudutils.get_collection(db, DOCTYPE_EV_GPQ)
    dic = data.dict()
    ts = round(time() * 1000)
    dic["saved"] = ts
    index = data.seq - 1
    docpath = "records." + str(index)
    # logging.info("docpath: " + retdoc)

    rs = await collection.find_one_and_update(
        { "_id": ObjectId(id) },
        { "$set": { "touched": ts, docpath: dic } },
        { "_id": 0, u"records": 1 },
        return_document=ReturnDocument.AFTER
    )
    if rs:
        return rs['records'][index]
    return None



