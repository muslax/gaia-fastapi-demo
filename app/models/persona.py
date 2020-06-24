from typing import Any, Dict, List, Optional, Union, Tuple

from bson.objectid import ObjectId
from pydantic import EmailStr, Schema, validator

from app.models.base import BaseModel, DBModel, LicenseModel, PRJModel, RWModel, UserModel
from app.models.user import User, UserBase


# class Status(BaseModel):
#     # id: str
#     ts: str
#     mod: str
#     seq: str
#     finished: bool


class Battery(BaseModel):
    """
    A Battery represents a module which has type (GPQ, CSI, etc)
    and a number of items.
    """
    type: str
    items: int
    touched: int


class Progress(BaseModel):
    state: str         # idle, working, paused, finished
    battery: str = None
    touched: int = None
    next: str = None


class PersonaInfo(BaseModel):
    fullname: str = None
    username: str = None
    email: EmailStr = None
    gender: str = None
    birth: str = None
    phone: str = None
    gender: str = None
    birth_date: str = None
    nip: str = None
    position: str = None
    current_level: str = None
    target_level: str = None


class PersonaBase(UserModel, LicenseModel):
    license: str
    gender: str = None
    birth_date: str = None
    nip: str = None
    position: str = None
    current_level: str = None
    target_level: str = None
    batteries: List[Battery] = []
    progress: Progress = None

    @validator('license')
    @classmethod
    def check_license(cls, v):
        if not (v=="gaia" or ObjectId.is_valid(v)):
            raise ValueError("Incorrect `license` value.")
        return v


# class ProjectModel(BaseModel):
#     prj_id: Optional[Any]

#     @validator("prj_id")
#     @classmethod
#     def validate_proid(cls, x):
#         return str(x)


class Persona(PersonaBase, PRJModel, DBModel):
    oid: Optional[Any] = Schema(..., alias="_id")

    @validator("oid")
    @classmethod
    def validate_id(cls, x):
        return str(x)


# class PersonaInDB(PersonaBase, ProjectModel):
class PersonaInDB(PersonaBase, PRJModel):
    prj_id: Optional[Any]
    hashed_password: str

    @validator("prj_id")
    @classmethod
    def validate_prj_id(cls, x):
        return ObjectId(x)


class PersonaCreate(PersonaBase):
    fullname: str
    username: str
    password: str
    email: EmailStr
    # batteries: List[str] = []


class ProjectPersona(PersonaCreate):
    prj_id: str


class PersonaUpdate(Persona):
    oid: Optional[Any] = None
    prj_id: Optional[Any] = None
    username: Optional[Any] = None


class PersonaResponse(BaseModel):
    response: Persona


class ManyPersonasResponse(BaseModel):
    response: List[Persona]
    count: int
