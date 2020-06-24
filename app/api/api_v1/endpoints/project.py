import logging
import random
from typing import Any, List

from bson.objectid import ObjectId
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorCollection as Collection
from pydantic import BaseModel, EmailStr
from pymongo import ReturnDocument

from app.api import utils
from app.api.security import (get_current_project_creator,
                              get_current_project_manager, get_current_user)
from app.core.config import (DATA_PAGING_DEFAULT, DOCTYPE_COMPANY,
                             DOCTYPE_PERSONA, DOCTYPE_PROJECT, USERTYPE_CLIENT,
                             USERTYPE_EXPERT)
from app.core.security import get_password_hash
from app.crud import project as crud
from app.crud.company import get as get_company
from app.crud.persona import create as create_persona
from app.crud.persona import create_multi as create_personas
from app.crud.persona import get_multi as get_multi_personas
from app.crud.persona import get_multi_filtered as get_multi_filtered_personas
from app.crud.utils import get_collection
from app.db.mongo import AsyncIOMotorClient as DBClient
from app.db.mongo import get_database
from app.models.base import Workbook
from app.models.batch import (Batch, BatchBase, BatchCreate, FacetimeSession,
                              WorkbookSession)
from app.models.persona import (Persona, PersonaCreate, PersonaInDB,
                                PersonaInfo, ProjectPersona)
from app.models.project import (Guest, GuestCreate, Project, ProjectBase,
                                ProjectCreate, ProjectInfo, ProjectUpdate)
from app.models.user import UserBase, UserInApp, UserInDB

router = APIRouter()

client = Depends(get_database)


@router.get("/all",
summary="Read all projects",
response_model=List[Project])
async def read_all_projects(
    limit: int=50,
    skip: int=0,
    db: DBClient=client):
    """Read projects"""
    logging.info(f">>> {__name__}:{read_project.__name__}")
    # filter = {'owner': current_user['context']}
    projects = await crud.get_multi(db, limit, skip)
    return projects


@router.get("",
summary="Read projects",
response_model=List[Project])
async def read_projects(
    limit: int=50,
    skip: int=0,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_creator)):
    """Read projects"""
    logging.info(f">>> {__name__}:{read_project.__name__}")
    filter = {'owner': current_user['context']}
    projects = await crud.get_multi_by_filter(db, filter, limit, skip)
    return projects


@router.post("",
response_model=Project)
async def create_project(
    data: ProjectInfo,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_creator)):
    """Create new project with full template"""
    logging.info(f">>> {__name__}:{create_project.__name__}")
    _dict = data.dict()
    client_id = _dict["client_id"]
    context = current_user['context']
    company = await get_company(db, client_id)
    if not company:
        return utils.create_422_response("Could not find the referred company")
    company_name = company["name"]
    _dict["client_name"] = company_name
    _dict["owner"] = context
    project = await crud.create(db, ProjectCreate(**_dict))
    if project:
        return project
        # return utils.create_aliased_response(ProjectResponse(response=project))
    return utils.create_500_response("Project creation failed")


@router.get("/{id}",
response_model=Project)
async def read_project(
    id: str,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_user)):
    """Read project info"""
    logging.info(f">>> {__name__}:{read_projects.__name__}")

    is_member = await crud.is_project_member(db, current_user, id)
    if not is_member:
        utils.raise_not_member()

    project = await crud.get(db, id)
    if project:
        return project

    return utils.create_404_response()


""" CLIENTS """

@router.get("/{id}/clients",
summary="Get project clients",
response_model=List[Guest])
async def read_clients(
    id: str,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_user)):
    logging.info(f">>> {__name__}:{read_clients.__name__}")

    is_member = await crud.is_project_member(db, current_user, id)
    if not is_member:
        utils.raise_not_member()

    return await crud.get_members(db, id, USERTYPE_CLIENT)


@router.post("/{id}/clients", # add-client
summary="Add project client",
response_model=Guest)
async def add_client(
    id: str,
    data: GuestCreate,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):
    """Add client to project.

    **TODO**: Email notification
    """
    logging.info(f">>> {__name__}:{add_client.__name__}")

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    free = await crud.check_free_member_slot(db, id, data.email, data.username)
    print("FREE: {}", free)
    if not free:
        return utils.error_400_response("Email or username already registered in project.")
    added = await crud.add_member(db, id, USERTYPE_CLIENT, data)
    print(added)
    if added:
        return utils.create_aliased_response(
            {"response": Guest(**added)}
        )
    return utils.create_aliased_response({"response": None})


@router.put("/{id}/clients", # edit-client
summary="[TODO] Edit project client",
response_model=Guest)
async def edit_client(
    id: str,
    username: str,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    return None


@router.delete("/{id}/clients", # delete-client
summary="[TODO] Delete project client",
response_model=Guest)
async def delete_client(
    id: str,
    username: str,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    return None


""" EXPERTS """

@router.get("/{id}/experts",
summary="Get project experts",
response_model=List[Guest])
async def read_experts(
    id: str,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_user)):
    logging.info(f">>> {__name__}:{read_clients.__name__}")

    is_member = await crud.is_project_member(db, current_user, id)
    if not is_member:
        utils.raise_not_member()

    return await crud.get_members(db, id, USERTYPE_EXPERT)


@router.post("/{id}/experts",
response_model=Guest)
async def add_expert(
    id: str,
    data: GuestCreate,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):
    """Add expert to project.

    **TODO**: Email notification
    """
    logging.info(f">>> {__name__}:{add_client.__name__}")

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    free = await crud.check_free_member_slot(db, id, data.email, data.username)
    print("FREE: {}", free)
    if not free:
        return utils.error_400_response("Email or username already registered in project.")
    added = await crud.add_member(db, id, USERTYPE_EXPERT, data)
    print(added)
    if added:
        return utils.create_aliased_response(
            {"response": Guest(**added)}
        )
    return utils.create_aliased_response({"response": None})


@router.put("/{id}/experts",
summary="[TODO] Edit project expert",
response_model=Guest)
async def edit_expert(
    id: str,
    username: str,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    return None


@router.delete("/{id}/experts",
summary="[TODO] Delete project expert",
response_model=Guest)
async def delete_expert(
    id: str,
    username: str,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    return None


""" PERSONA """

@router.get("/{id}/personas",
response_model=List[Persona])
async def read_project_personas(
    id: str,
    limit: int = DATA_PAGING_DEFAULT,
    skip: int = 0,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_user)):
    """
    Read project personas.
    """
    logging.info(f">>> {__name__}:{read_project_personas.__name__}")

    is_member = await crud.is_project_member(db, current_user, id)
    if not is_member:
        utils.raise_not_member()

    personas = await get_multi_filtered_personas(db, {"prj_id": ObjectId(id)}, limit, skip)
    return personas


@router.post("/{id}/personas",
response_model=BaseModel)
async def add_persona(id: str,
    fullname: str = Body(...),
    username: str = Body(...),
    email: EmailStr = Body(...),
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):
    """
    Create project persona.
    """

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    f1 = username[:3]
    f2 = str(ObjectId())[20:]
    f2 = ''.join(random.sample(f2, len(f2)))
    password = f1 + f2
    hashed_password = get_password_hash(password)
    persona = PersonaInDB(
        prj_id = ObjectId(id),
        license = 'gaia',
        fullname = fullname,
        username = username,
        password = password,
        email = email,
        note = password[::-1],
        hashed_password = hashed_password
    )
    persona = await create_persona(db, persona)
    print(persona)
    return utils.create_aliased_response(Persona(**persona))


@router.put("/{id}/personas",
summary="[TODO] Edit project persona",
response_model=Guest)
async def edit_persona(
    id: str,
    user_id: str,
    info: PersonaInfo,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    return None


@router.delete("/{id}/personas",
summary="[TODO] Delete project persona",
response_model=Guest)
async def delete_persona(
    id: str,
    user_id: str,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    return None


""" MODULES """

@router.get("/{id}/modules",
summary="Read project modules",
response_model=List[Workbook])
async def read_modules(
    id: str,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_user)):
    logging.info(f">>> {__name__}:{read_modules.__name__}")

    is_member = await crud.is_project_member(db, current_user, id)
    if not is_member:
        utils.raise_not_member()

    return await crud.get_modules(db, id)


@router.get("/{id}/workbooks",
summary="Read project workbook modules",
response_model=List[Workbook])
async def read_workbooks(
    id: str,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_user)):
    logging.info(f">>> {__name__}:{read_workbooks.__name__}")

    is_member = await crud.is_project_member(db, current_user, id)
    if not is_member:
        utils.raise_not_member()

    return await crud.get_modules(db, id, "workbook")


@router.post("/{id}/workbooks",
summary="Add project workbook",
response_model=Workbook)
async def add_workbook(
    id: str,
    data: Workbook,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):
    """Add workbook module to project"""
    logging.info(f">>> {__name__}:{add_workbook.__name__}")

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    collection = get_collection(db, DOCTYPE_PROJECT)
    found = await collection.find_one(
        {
            "_id": ObjectId(id),
            "workbooks.type": data.type
        },
        {"_id": 0, "workbooks.$": 1}
    )
    print(found)
    if found:
        raise HTTPException(
            status_code=400,
            detail="The module with given type already exists in project."
        )
    rs = await crud.add_module(db, id, data, False)
    return rs


@router.put("/{id}/workbooks",
summary="Edit project workbook",
response_model=Workbook)
async def edit_workbook(id: str, type: str,
    version: str=Body(...),
    title: str=Body(...),
    items: int=Body(...),
    uri: str=Body(...),
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):
    logging.info(f">>> {__name__}:{edit_workbook.__name__}")

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    info = {
        'type': type,
        'version': version,
        'title': title,
        'items': items,
        'uri': uri
    }
    return await crud.edit_workbook(db, id, type, info)


@router.delete("/{id}/workbooks",
summary="Delete project workbook",
response_model=List[Workbook])
async def delete_workbook(
    id: str,
    type: str,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):
    """Return list of workbooks after deletion."""
    logging.info(f">>> {__name__}:{delete_workbook.__name__}")

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    return await crud.delete_workbook(db, id, type)


@router.get("/{id}/facetimes",
summary="Read project facetime modules",
response_model=List[Workbook])
async def read_facetimes(
    id: str,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_user)):
    logging.info(f">>> {__name__}:{read_facetimes.__name__}")

    is_member = await crud.is_project_member(db, current_user, id)
    if not is_member:
        utils.raise_not_member()

    return await crud.get_modules(db, id, "facetime")


@router.post("/{id}/facetimes",
summary="Add project facetime module",
response_model=Workbook)
async def add_facetime(
    id: str,
    data: Workbook,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):
    """Add facetime module to project"""
    logging.info(f">>> {__name__}:{add_facetime.__name__}")

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    collection = get_collection(db, DOCTYPE_PROJECT)
    found = await collection.find_one(
        {
            "_id": ObjectId(id),
            "facetimes.type": data.type
        },
        {"_id": 0, "facetimes.$": 1}
    )
    print(found)
    if found:
        raise HTTPException(
            status_code=400,
            detail="The module with given type already exists in project."
        )
    rs = await crud.add_module(db, id, data, True)
    return rs


@router.put("/{id}/facetimes",
summary="Edit project facetime",
response_model=Workbook)
async def edit_facetime(id: str, type: str,
    version: str=Body(...),
    title: str=Body(...),
    items: int=Body(...),
    uri: str=Body(...),
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):
    logging.info(f">>> {__name__}:{edit_facetime.__name__}")

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    info = {
        'type': type,
        'version': version,
        'title': title,
        'items': items,
        'uri': uri
    }
    return await crud.edit_facetime(db, id, type, info)


@router.delete("/{id}/facetimes",
summary="Delete project facetime",
response_model=List[Workbook])
async def delete_facetime(
    id: str,
    type: str,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):
    """Return list of facetimes after deletion."""
    logging.info(f">>> {__name__}:{delete_facetime.__name__}")

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    return await crud.delete_facetime(db, id, type)


async def add_modules(id: str, data: List[Workbook], db: DBClient=client):
    """Add one or more modules to project"""
    logging.info(f">>> {__name__}:{add_modules.__name__}")
    added = await crud.add_modules(db, id, data)
    if added:
        return utils.create_aliased_response(
            {"response": added, "count": len(added)}
        )
    return utils.create_aliased_response({"response": [], "count": 0})


# @router.post("/projects/{id}/add-note")
async def add_note(id: str, note: str, db: DBClient=client):
    """Add note/comment to project"""
    logging.info(f">>> {__name__}:{add_note.__name__}")
    rs = await crud.add_note(db=db, prj_id=id, note=note)
    return {"response": rs}


""" BATCH """

@router.get("/{id}/batches",
summary="Read project batches",
response_model=List[Batch])
async def read_batches(
    id: str,
    db: DBClient=client,
    current_user: UserInApp=Depends(get_current_user)):
    """Read project batches."""
    logging.info(f">>> {__name__}:{read_batches.__name__}")

    is_member = await crud.is_project_member(db, current_user, id)
    if not is_member:
        utils.raise_not_member()

    return await crud.get_batches(db, id)


@router.post("/{id}/create-batch",
response_model=Batch)
async def create_batch(id: str, data: BatchCreate, db: DBClient = client,
    current_user: UserInDB=Depends(get_current_project_manager)):
    """Create batch for group of participants"""
    logging.info(f">>> {__name__}:{create_batch.__name__}")

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    rs = await crud.create_batch(db=db, id=id, data=data)
    # return {"response": rs}
    return rs


@router.put("/{id}/add-batch-workbook",
response_model=WorkbookSession)
async def add_workbook_session(id: str, batch_id: str, data: WorkbookSession,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):
    """Add workbook session to batch"""
    logging.info(f">>> {__name__}:{add_workbook_session.__name__}")

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    # Check if module is already there
    collection = get_collection(db, DOCTYPE_PROJECT)
    found = await collection.find_one(
        {
            "_id": ObjectId(id),
            "batches.batch_id": batch_id,
            "batches.workbook_sessions.module": data.module
        },
        {"_id": 0, "batches": {"$elemMatch": {"batch_id": batch_id}}}
    )
    # print(found)
    if found:
        raise HTTPException(
            status_code=400,
            detail="The module with given type already exists in the batch."
        )
    rs = await crud.add_workbook_session(db, id, batch_id, data)
    return rs


@router.put("/{id}/add-workbook-facetime",
response_model=FacetimeSession)
async def add_facetime_session(id: str, batch_id: str, data: FacetimeSession,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):
    """Add facetime session to batch"""
    logging.info(f">>> {__name__}:{add_facetime_session.__name__}")

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    # Check if module is already there
    collection = get_collection(db, DOCTYPE_PROJECT)
    found = await collection.find_one(
        {
            "_id": ObjectId(id),
            "batches.batch_id": batch_id,
            "batches.facetime_sessions.module": data.module
        },
        {"_id": 0, "batches": {"$elemMatch": {"batch_id": batch_id}}}
    )
    if found:
        raise HTTPException(
            status_code=400,
            detail="The module with given type already exists in the batch."
        )

    rs = await crud.add_facetime_session(db, id, batch_id, data)
    return rs


async def add_personas(id: str, data: List[PersonaCreate], db: DBClient=client):
    """Add one or more participants to projects

    [NOT COMPLETED]"""
    logging.info(f">>> {__name__}:{add_personas.__name__}")
    docs = []
    for p in data:
        _dict = p.dict()
        del _dict["password"]
        dic = {
            "prj_id": ObjectId(id),
            **_dict,
            "hashed_password": get_password_hash(p.password)
        }
        docs.append(dic)
    _ids = await create_personas(db, docs)
    ids = []
    for x in _ids:
        ids.append(str(x))
    return utils.create_aliased_response({"response": ids, "count": len(ids)})


@router.put("/{id}/prepare-batteries",
summary="Prepare persona batteries")
async def prepare_batteries(id: str, batch_id: str, db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):
    """Update persona data to match batch project"""
    logging.info(f">>> {__name__}:{prepare_batteries.__name__}")

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    rs = await crud.prepare_persona_batteries(db, id, batch_id)
    return rs


@router.put("/{id}/prepare-evidences",
summary="Prepare persona evidences")
async def prepare_evidences(id: str, batch_id: str, db: DBClient=client,
    current_user: UserInDB=Depends(get_current_project_manager)):
    """Create persona evidence templates"""
    logging.info(f">>> {__name__}:{prepare_evidences.__name__}")

    is_manager = await crud.is_project_manager(db, current_user, id)
    if not is_manager:
        utils.raise_not_manager()

    rs = await crud.prepare_persona_evidences(db, id, batch_id)
    return rs
