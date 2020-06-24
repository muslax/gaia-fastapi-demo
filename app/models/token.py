from pydantic import BaseModel
# from bson.objectid import ObjectId


class Token(BaseModel):
    access_token: str
    token_type: str
    # user: dict

class Token2(BaseModel):
    access_token: str
    token_type: str
    user: dict


class TokenPayload(BaseModel):
    username: str = None
    scope: str = None
    # channel: str = None
    context: str = None
