from typing import Any, List, Optional

from pydantic import EmailStr, validator

from app.core.config import COMPANY_SYMBOL_LENGTH
from app.models.base import BaseModel, DBModel, RWModel, UserModel


class Contact(BaseModel):
    fullname: str
    email: EmailStr = None
    gender: str = None
    birth: str = None
    phone: str = None
    note: str = None


class CompanyBase(RWModel):
    created_by: str  # gaia or id of license holder
    name: str = None
    symbol: str = None
    org_type: str = None
    industry: List[str] = []
    products: List[str] = []
    description: str = None
    address: str = None
    homepage: str = None
    email: EmailStr = None
    phone: str = None
    contacts: List[Contact] = []

    @validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        if not (len(v) == COMPANY_SYMBOL_LENGTH and v.isalnum()):
            raise ValueError('Symbol must be alpha and contain 5 character')
        return v.upper()


class Company(CompanyBase, DBModel):
    created_by: str     # index
    name: str           # index
    symbol: str


class CompanyCreate(CompanyBase):
    created_by: Optional[Any] = None
    name: str
    symbol: str


class CompanyUpdate(CompanyBase):
    symbol: Optional[Any] = None


class CompanyResponse(RWModel):
    response: Company


class ManyCompaniesResponse(RWModel):
    response: List[Company]
    count: int
