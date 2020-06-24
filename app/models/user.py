from typing import Any, List, Optional

from pydantic import EmailStr, validator

from app.core.config import (
    USERTYPE_GAIA,
    USERTYPE_LICENSE,
    USERTYPE_CLIENT,
    USERTYPE_EXPERT,
    USERTYPE_PERSONA,
    USERNAME_MIN_LENGTH,
    USERNAME_MAX_LENGTH
)
from app.models.base import (
    BaseModel,
    ContextModel,
    DBModel,
    RWModel,
    TypedModel,
    UserModel
)


class UserBase(UserModel, TypedModel):
    admin_roles: List[str] = None

    @validator('type')
    @classmethod
    def check_type(cls, v):
        if not (v == USERTYPE_GAIA or v == USERTYPE_LICENSE):
            raise ValueError('Type must be `gaia` or `license`')
        return v

    @validator('username')
    @classmethod
    def validate_username(cls, v):
        if not (len(v) >= USERNAME_MIN_LENGTH
        and len(v) <= USERNAME_MAX_LENGTH
        and v.isalnum()):
            raise ValueError('Must be alphanumeric, 5-10 characters length')
        return v.lower()


class User(UserBase, DBModel):
    """DBModel: have _id"""
    admin_roles: List[str] = None


class UserWithContext(User, ContextModel):
    context: str = None

    @validator('type')
    @classmethod
    def check_type(cls, v):
        if not (
            v == USERTYPE_GAIA or
            v == USERTYPE_LICENSE or
            v == USERTYPE_CLIENT or
            v == USERTYPE_EXPERT or
            v == USERTYPE_PERSONA):
            raise ValueError('Unrecognized user type')
        return v


class UserInDB(UserBase):
    fullname: str
    username: str
    email: EmailStr
    disabled: bool = False
    hashed_password: str
    admin_roles: List[str] = []


class UserInApp(UserModel, TypedModel):
    fullname: str
    username: str
    email: EmailStr
    disabled: bool = False
    hashed_password: str
    admin_roles: List[str] = []

    @validator('type')
    @classmethod
    def check_type(cls, v):
        if not (
            v == USERTYPE_GAIA or
            v == USERTYPE_LICENSE or
            v == USERTYPE_CLIENT or
            v == USERTYPE_EXPERT or
            v == USERTYPE_PERSONA):
            raise ValueError('Unrecognized user type')
        return v


class UserCreate(UserBase):
    type: Optional[Any] = None
    username: str
    password: str
    email: EmailStr
    admin_roles: List[str] = []


class UserUpdate(UserBase):
    username: Optional[Any] = None
    password: Optional[str] = None
    admin_roles: List[str] = []


class UserResponse(BaseModel):
    response: User


class ManyUsersResponse(BaseModel):
    response: List[User]
    count: int
