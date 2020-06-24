import logging
from typing import List

from bson.objectid import ObjectId
from fastapi import APIRouter, Depends

from app.api import utils
from app.core.config import DOCTYPE_PROJECT
from app.core.security import get_password_hash
from app.crud import persona as crud
from app.crud.project import get as get_project
from app.db.mongo import AsyncIOMotorClient as DBClient
from app.db.mongo import get_database
from app.models.persona import ( BaseModel, Battery,
    Persona, PersonaCreate, PersonaInDB, PersonaUpdate,
    PersonaResponse, ManyPersonasResponse
)
# from app.models.person import PersonTest, PersonUser

router = APIRouter()

client = Depends(get_database)


@router.get("/personas",
summary="Read personas",
response_model=List[Persona])
async def read_personas(limit: int=50, skip: int=0, db: DBClient=client):
    """Read personas"""
    logging.info(f">>> {__name__}:{read_personas.__name__}")
    personas = await crud.get_multi(db, limit, skip)
    # personas = await crud.get_multi_filtered(db, {"prj_id": ObjectId("5e870e7d4c789fb7d8301909")}, limit, skip)
    return utils.create_aliased_response(
        ManyPersonasResponse(response=personas, count=len(personas))
    )


# @router.get("/personas/{prj_id}/personas", response_model=List[Persona])
async def read_project_personas(prj_id: str, limit: int=50, skip: int=0, db: DBClient=client):
    """Read project personas"""
    logging.info(f">>> {__name__}:{read_project_personas.__name__}")
    prj_id = ObjectId(prj_id)
    personas = await crud.get_multi_filtered(db, {"prj_id": prj_id}, limit, skip)
    return utils.create_aliased_response(
        ManyPersonasResponse(response=personas, count=len(personas))
    )


@router.post("/personas", response_model=Persona)
async def create_persona(prj_id: str, data: PersonaCreate, db: DBClient=client):
    """Create new persona"""
    logging.info(f">>> {__name__}:{create_persona.__name__}")
    project = await get_project(db, prj_id)
    if not project:
        return utils.create_422_response("Could not find the referred project")

    hashed_pwd = get_password_hash(data.password)
    _dict = data.dict()
    _dict["prj_id"] = prj_id
    _dict["hashed_password"] = hashed_pwd
    logging.info(">>> ================")
    model = PersonaInDB(**_dict)
    logging.info(">>> ================")
    persona = await crud.create(db, model)
    if persona:
        return utils.create_aliased_response(PersonaResponse(response=persona))
    return utils.create_500_response("Persona creation failed")


@router.post("/personas/{id}",
summary="Set persona batteries",
response_model=List[Battery])
async def set_batteries(id: str, batteries: List[Battery], db: DBClient=client):
    """Define batteries for persona"""
    logging.info(f">>> {__name__}:{set_batteries.__name__}")
    return await crud.set_batteries(db, id, batteries)


@router.get("/personas/{ref}", response_model=Persona)
async def read_persona(ref: str, db: DBClient=client):
    """Read persona info"""
    logging.info(f">>> {__name__}:{read_persona.__name__}")
    persona = await crud.get(db, ref)
    if persona:
        return utils.create_aliased_response(PersonaResponse(response=persona))
    return utils.create_404_response()


@router.put("/personas/{ref}", response_model=Persona)
async def update_persona(ref: str, data: PersonaUpdate, db: DBClient=client):
    """Update persona info"""
    logging.info(f">>> {__name__}:{update_persona.__name__}")
    persona = await crud.get(db, ref)
    if not persona:
        return utils.create_404_response()

    updated = await crud.update(db, persona["_id"], data)
    if updated:
        return utils.create_aliased_response(PersonaResponse(response=updated))
    return utils.create_422_response()
