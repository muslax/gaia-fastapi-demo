from datetime import datetime, timezone
from typing import Any, List, Optional

from pydantic import BaseConfig, BaseModel, EmailStr, Schema, validator

from app.core.config import USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH


class RWModel(BaseModel):
    class Config(BaseConfig):
        allow_population_by_alias = True
        json_encoders = {
            datetime: lambda dt: dt.replace(tzinfo=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
            }


class ClientModel(BaseModel):
    client_id: Optional[Any]

    @validator("client_id")
    @classmethod
    def validate_client_id(cls, x):
        return str(x)


class DBModel(BaseModel):
    oid: Optional[Any] = Schema(..., alias="_id")

    @validator("oid")
    @classmethod
    def validate_id(cls, x):
        return str(x)


class PRJModel(BaseModel):
    prj_id: Optional[Any]

    @validator("prj_id")
    @classmethod
    def validate_proid(cls, x):
        return str(x)


class UserModel(BaseModel):
    fullname: str = None
    username: str = None
    email: EmailStr = None
    gender: str = None
    birth: str = None
    phone: str = None
    note: str = None
    disabled: bool = False

    @validator('username')
    @classmethod
    def validate_username(cls, v):
        if not (len(v) >= USERNAME_MIN_LENGTH
        and len(v) <= USERNAME_MAX_LENGTH
        and v.isalnum()):
            raise ValueError('Must be alphanumeric, 5-10 characters length')
        return v.lower()


class TypedModel(BaseModel):
    type: str = None


class ContextModel(BaseModel):
    context: str = None


class LicenseModel(BaseModel):
    license: str = None


class Note(BaseModel):
    content: str = None
    note_by: str = None  # fullname
    note_date: datetime = None
    note_username: str = None  # username
    is_public: bool = True


class Vocabulary(BaseModel):
    phrase: str
    description: str = None


class Enum(BaseModel):
    organization_type: List[Vocabulary] = []
    industry: List[Vocabulary] = []
    project_type: List[Vocabulary] = []
    project_domain: List[Vocabulary] = []
    modules: List[Vocabulary] = []


class Workbook(BaseModel):
    type: str
    version: str = None
    """title = branding label"""
    title: str = None
    items: int
    """mode = autonomous / facetime"""
    # mode: str = "autonomous"
    uri: str = None

    @validator("type")
    @classmethod
    def validate_type(cls, v):
        return v.upper()
