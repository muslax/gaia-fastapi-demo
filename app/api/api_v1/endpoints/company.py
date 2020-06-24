import logging
# import jwt
# from jwt import PyJWTError
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException

from app.api import utils
from app.crud import company as crud
from app.db.mongo import AsyncIOMotorClient as DBClient
from app.db.mongo import get_database
from app.models.base import UserModel
from app.models.user import UserBase, UserInDB
from app.models.company import (
    BaseModel, Contact,
    Company, CompanyBase, CompanyCreate, CompanyResponse,
    CompanyUpdate, ManyCompaniesResponse
)
from app.api.security import get_current_user



router = APIRouter()

client = Depends(get_database)


@router.get("/companies",
summary="Read companies",
response_model=List[Company])
async def read_companies(
    limit: int=50,
    skip: int=0,
    db: DBClient=client,
    # current_user: UserInDB=Depends(get_current_user)
    ):
    """Read companies"""
    logging.info(f">>> {__name__}:{read_companies.__name__}")
    # context = current_user['context']
    # Filter by user context
    filter = {}
    companies = await crud.get_multi_by_filer(db, filter, limit, skip)
    return companies
    # return utils.create_aliased_response(
    #     ManyCompaniesResponse(response=companies, count=len(companies))
    # )


@router.get("/companies-by-license",
summary="Read companies by license",
response_model=List[Company])
async def read_companies_by_license(
    limit: int=50,
    skip: int=0,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_user)
    ):
    """Read companies"""
    logging.info(f">>> {__name__}:{read_companies_by_license.__name__}")
    context = current_user['context']
    # Filter by user context
    filter = {"created_by": context}
    companies = await crud.get_multi_by_filer(db, filter, limit, skip)
    return companies
    # return utils.create_aliased_response(
    #     ManyCompaniesResponse(response=companies, count=len(companies))
    # )


@router.post("/companies", response_model=Company)
async def create_company(
    data: CompanyCreate,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_user)):
    """Create new company"""
    logging.info(f">>> {__name__}:{create_company.__name__}")
    context = current_user['context']
    data.created_by = context
    # print(data)
    company = await crud.create(db, data)
    if company:
        return utils.create_aliased_response(CompanyResponse(response=company))
    return utils.create_500_response("Company creation failed")


@router.get("/companies/{ref}", response_model=Company)
async def read_company(ref: str, db: DBClient=client):
    """Read company info"""
    logging.info(f">>> {__name__}:{read_company.__name__}")
    company = await crud.get(db, ref)
    if company:
        return utils.create_aliased_response(CompanyResponse(response=company))
    return utils.create_404_response()


@router.put("/companies/{ref}", response_model=Company)
async def update_company(ref: str, data: CompanyUpdate, db: DBClient=client):
    """Update company info"""
    logging.info(f">>> {__name__}:{update_company.__name__}")
    found = await crud.get(db, ref)
    if not found:
        return utils.create_404_response()
    company = await crud.update(db, found["_id"], data)
    if company:
        return utils.create_aliased_response(CompanyResponse(response=company))
    return utils.create_422_response()


@router.post("/companies/{ref}/add-contacts", response_model=List[Contact])
async def add_contacts(ref: str, data: List[Contact], db: DBClient=client):
    """Add one or more contacts to company"""
    logging.info(f">>> {__name__}:{add_contacts.__name__}")
    updated = await crud.add_contacts(db, ref, data)
    if updated:
        return utils.create_aliased_response(
            {"response": updated, "count": len(updated)}
        )
    return utils.create_aliased_response({"response": [], "count": 0})


@router.post("/companies/{ref}/remove-contact", response_model=List[Contact])
async def remove_contact(ref: str, contact: dict, db: DBClient=client):
    """
    Example dict: `{"email": "eseym@example.com"}`
    """
    logging.info(f">>> {__name__}:{remove_contact.__name__}")
    removed = await crud.remove_contact(db, ref, contact)
    # print(removed)
    return utils.create_aliased_response({"response": removed})
