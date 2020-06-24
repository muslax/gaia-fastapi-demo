from datetime import datetime
from typing import Any, List, Optional

from bson.objectid import ObjectId
from pydantic import Schema, validator

from app.models.dbmodel import BaseModel, DBModel, RWModel


class GPQRow(BaseModel):
    """`saved` & `elapsed` must come from identical time source"""
    seq: int
    wb_seq: int             # nomer urut di workbook
    element: str = None     # simbol elemen
    statement: str = None   # Lorem ipsum...
    saved: int = None       # time when record was saved
    elapsed: int = None     # elapsed time since previous event


class GPQEvidenceBase(RWModel):
    prj_id: Optional[Any] = None
    # version: str = None
    username: str = None
    fullname: str = None
    initiated: int = None
    started: int = None
    stopped: int = None
    touched: int = None
    records: List[GPQRow] = []


class GPQEvidence(GPQEvidenceBase, DBModel):
    oid: Optional[Any] = Schema(..., alias="_id")
    prj_id: Optional[Any]
    username: str
    # fullname: str

    @validator("prj_id")
    @classmethod
    def validate_prj_id(cls, x):
        return str(x)

    @validator("oid")
    @classmethod
    def validate_id(cls, x):
        return str(x)


class GPQEvidenceInDB(GPQEvidenceBase):
    prj_id: Optional[Any]
    username: str
    fullname: str

    @validator("prj_id")
    @classmethod
    def validate_prj_id(cls, x):
        return ObjectId(x)


class GPQEvidenceResponse(RWModel):
    response: GPQEvidence


class ManyGPQEvidencesResponse(RWModel):
    response: List[GPQEvidence]
    count: int
