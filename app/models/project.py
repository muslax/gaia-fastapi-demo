from typing import Any, List, Optional

from bson.objectid import ObjectId
from pydantic import EmailStr, Schema, validator

from app.models.batch import Batch
from app.models.base import (
    BaseModel,
    ClientModel,
    DBModel,
    RWModel,
    TypedModel,
    UserModel,
    Workbook
)


class Guest(UserModel, TypedModel, DBModel):
    """Has type and id"""
    type: str
    fullname: str
    username: str
    email: EmailStr


class GuestCreate(UserModel, TypedModel):
    type: Optional[Any] = None
    password: str


# class GuestInDB(Guest):
#     hashed_password: str


class ProjectInfo(RWModel):
    client_id: str
    year: int = None
    title: str = None
    status: str = "open"
    description: str = None
    domain: str = None
    type: str = None
    lead_by: str = None
    contract: str = None
    signed_by: str = None
    start_date: str = None
    end_date: str = None
    ext_date: str = None
    payment_terms: str = None
    potential_value: float = None
    actual_value: float = None


class ProjectBase(RWModel):
    owner: str  # gaia or id of license holder
    year: int = None
    title: str = None
    client_name: str = None
    status: str = "open"
    description: str = None
    domain: str = None
    type: str = None
    lead_by: str = None
    contract: str = None
    signed_by: str = None
    start_date: str = None
    end_date: str = None
    ext_date: str = None
    payment_terms: str = None
    potential_value: float = None
    actual_value: float = None
    inv_dates: List[str] = []
    #
    # notes: List[str] = []
    members: List[Guest] = []
    # modules: List[Workbook] = []
    # workbooks is for so-called paper-n-pencil tests
    workbooks: List[Workbook] = []
    # facetimes is for interview, discussion, and presentation
    facetimes: List[Workbook] = []
    # batches: dict = {}
    batches: List[Batch] = []


class Project(ProjectBase, ClientModel, DBModel):
    pass


class ProjectInDB(ProjectBase, ClientModel):
    client_id: Optional[Any]

    @validator("client_id")
    @classmethod
    def validate_client_id(cls, x):
        return ObjectId(x)


class ProjectCreate(ProjectBase, ClientModel):
    client_id: str
    year: int
    title: str
    client_name: Optional[Any] = None


class ProjectUpdate(ProjectBase):
    title: str = None
    client_name: Optional[Any] = None


class ProjectResponse(RWModel):
    response: Project


class ManyProjectsResponse(RWModel):
    response: List[Project]
    count: int
