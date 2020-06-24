import logging
from time import time
from random import shuffle
from typing import List

from fastapi import APIRouter, Body, Depends
from bson.objectid import ObjectId

from app.api import utils
from app.core.config import DOCTYPE_EV_GPQ, DOCTYPE_PERSONA, GPQ_TOTAL_ITEMS
from app.crud.utils import get_by_dict, get_collection
from app.crud import gpq as crud
from app.crud.persona import get as get_persona, update_progress
from app.db.mongo import AsyncIOMotorClient as DBClient, get_database
from app.models.pev.gpq import (
    GPQEvidence, GPQEvidenceResponse, ManyGPQEvidencesResponse, GPQRow
)
from app.models.persona import Progress


router = APIRouter()

client = Depends(get_database)


"""
{
  "prj_id": "5e8760330541ba20d1901387",
  "username": "giyanti",
  "fullname": "Gina Ludwig Ayanti"
}"""

# /gpq
# /gpq/by-project/{5e8760330541ba20d1901387}
# /gpq/create           called on persona creation
# /gpq/id/              read
# /gpq/id/init          called when entering GPQ
# /gpq/id/start         called when starting workbook
# /gpq/id/update        called when sending answer
# /gpq/id/finish        called when finishing workbook



@router.get("/gpq",
summary="Read evidences",
response_model=List[GPQEvidence])
async def read_evidences(limit: int=50, skip: int=0, db: DBClient=client):
    logging.info(f">>> {__name__}:{read_evidences.__name__}")
    evidences = await crud.get_multi(db, limit, skip)
    return utils.create_aliased_response(
        ManyGPQEvidencesResponse(response=evidences, count=len(evidences))
    )


@router.get("/gpq/by-project/{id}",
summary="Read evidences by project",
response_model=List[GPQEvidence])
async def read_by_project(
    id: str, limit: int=50, skip: int=0, db: DBClient=client
    ):
    logging.info(f">>> {__name__}:{read_by_project.__name__}")
    if not ObjectId.is_valid(id):
        return utils.create_422_response("Invalid ObjectId")
    evidences = await crud.get_by_project(db, id, limit, skip)
    return utils.create_aliased_response(
        ManyGPQEvidencesResponse(response=evidences, count=len(evidences))
    )


# {
#   "prj_id": "5e870e7d4c789fb7d8301909",
#   "username": "persona4",
#   "rows": 120
# }

@router.post("/gpq/create",
summary="Create data template",
response_model = GPQEvidence)
async def create(
    prj_id: str = Body(...),
    username: str = Body(...),
    rows: int = Body(GPQ_TOTAL_ITEMS),
    db: DBClient = client):

    logging.info(f">>> {__name__}:{create.__name__}")
    collection = get_collection(db, DOCTYPE_PERSONA)
    persona = await get_by_dict(collection, {
        "prj_id": ObjectId(prj_id),
        "username": username
    })
    if not persona:
        return utils.create_422_response("Coul not verify project and/or persona")

    if not rows or rows == 0:
        rows = GPQ_TOTAL_ITEMS

    fullname = persona["fullname"]
    rs = await crud.create_template(db, prj_id, username, fullname, rows)
    if not rs:
        return utils.create_500_response("GPQ template creation failed")
    return utils.create_aliased_response(
        GPQEvidenceResponse(response=rs)
    )


# This should depend on current persona

@router.post("/gpq/init",
summary="Start session")
async def init(id: str, db: DBClient = client):
    rs = await crud.init(db, id)
    if not rs:
        return utils.create_500_response("GPQ update-init failed")
    return { "response": rs }


@router.post("/gpq/start",
summary="Start working on workbook")
async def start(id: str, db: DBClient = client):
    rs = await crud.start(db, id)
    if not rs:
        return utils.create_500_response("GPQ update-start failed")
    return { "response": rs }

# {
#   "seq": 4,
#   "wb_seq": 99,
#   "element": "SN",
#   "statement": "Manjaring datang jurang",
#   "last_touch": 1586143502687
# }
# {
#   "response": {
#     "touched": 1586154720892
#   }
# }

@router.post("/gpq/update",
summary="Save answer")
async def update(
    id: str,
    seq: int = Body(...),
    wb_seq: int = Body(...),
    element: str = Body(...),
    statement: str = Body(...),
    db: DBClient = client
    ):
    rs = await crud.update(db, id, seq, wb_seq, element, statement)
    if not rs:
        return utils.create_500_response("GPQ update-start failed")
    return { "response": rs }


