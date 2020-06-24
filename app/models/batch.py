from datetime import datetime
from typing import Any, List, Optional
from pydantic import Schema, validator

from app.models.base import BaseModel, DBModel, RWModel


class Pairing(BaseModel):
    asesi: str  # username
    asesor: str  # username


class Schedule(BaseModel):
    module: str                 # GPQ / GMATE / etc
    start_date: datetime = None
    end_date: datetime = None
    type: str = None  # in-house / client / public
    notes: str = None


class Facetime(RWModel):
    persona: str
    start_time: datetime
    duration: int


class Turn(RWModel):
    username: str
    start_time: datetime = None


class FacetimeSession(RWModel):
    # method: str
    module: str
    module_items: int = None
    panel: List[str] = []
    roster: List[Turn] = []

    @validator("module")
    @classmethod
    def validate_module(cls, v):
        return v.upper()


class WorkbookSession(RWModel):
    # workbook: str
    module: str
    module_items: int = None
    # items: int
    start_time: datetime = None
    duration: int
    panel: List[str] = []

    @validator("module")
    @classmethod
    def validate_module(cls, v):
        return v.upper()


class BatchBase(RWModel):
    lead_by: str = None
    start_time: datetime = None
    end_time: datetime = None
    participants: List[str] = []
    workbook_sessions: List[WorkbookSession] = []
    facetime_sessions: List[FacetimeSession] = []


class BatchModel(BaseModel):
    batch_id: Optional[Any]

    @validator("batch_id", check_fields=False)
    @classmethod
    def validate_id(cls, x):
        return str(x)


class Batch(BatchBase, BatchModel):
    pass


class BatchCreate(BaseModel):
    lead_by: str = None
    start_time: datetime = None
    end_time: datetime = None
    participants: List[str]


"""
Turn:
    username:
    start_time:

-autopilot
-facetime_session:
    method: presentation
    panel: hya, sri, mmo
    roster: [

    ]




mongo date

"2020-04-16T09:00:00+07:00",      "2020-04-16T02:00:00Z",
"2020-04-17T17:00:00.569+07:00",  "2020-04-17T10:00:00.569000Z",

"start_time": "2020-04-16T08:30:00+07",
"start_time": "2020-04-16T01:30:00Z",

"end_time": "2020-04-17T16:30:00+07",
"end_time": "2020-04-17T09:30:00Z",



projects/[id]/create-batch(lead, participants)
projects/[id]/[batch]/add-workbook
projects/[id]/[batch]/add-participants (usernames)

projects/[id]/[batch]/add-workbook-class
projects/5e8f416c5860cf44487f8f1b/5e8f8a16b75f0453cd8eceb8/add-workbook-class
projects/[id]/[batch]/add-facetime-class

batches/5e8f8a16b75f0453cd8eceb8/add-facetime-class

"""