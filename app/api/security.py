import jwt
import logging

from fastapi import HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from starlette.status import HTTP_403_FORBIDDEN
from bson.objectid import ObjectId

from app import crud
from app.core.config import USERTYPE_GAIA
from app.core.config import USERTYPE_LICENSE
from app.core.config import USERTYPE_CLIENT
from app.core.config import USERTYPE_EXPERT
from app.core.config import USERTYPE_PERSONA
from app.core.config import SECRET_KEY
from app.core.config import DOCTYPE_PERSONA, DOCTYPE_PROJECT, DOCTYPE_USER
from app.core.jwt import ALGORITHM
from app.db.mongo import get_database
# from app.models.context import ProjectContext
from app.models.token import TokenPayload
from app.models.user import User, UserInApp, UserInDB
from app.crud.project import get_project_member
from app.crud.utils import get_collection


# context = ProjectContext()
# currentUser = Security(get_current_user)

reuseable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/access-token",    # tokenUrl="/api/v1/login",
    scopes={
        USERTYPE_GAIA: "Gaia internal",
        USERTYPE_LICENSE: "License holder",
        USERTYPE_CLIENT: "Client",
        USERTYPE_EXPERT: "Project expert",
        USERTYPE_PERSONA: "Persona"
    }
)

async def get_current_user(token: str = Security(reuseable_oauth2)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except PyJWTError:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )
    db = get_database()

    # ? CAN'T USE -> user = crud.user.get(db, username=token_data.username)
    logging.info("USERNAME : " + token_data.username)
    logging.info("SCOPE: " + token_data.scope)
    logging.info("CONTEXT: " + token_data.context)
    scope = token_data.scope
    if scope == USERTYPE_PERSONA:
        collection = get_collection(db, DOCTYPE_PERSONA)
        user = await collection.find_one({
            "username": token_data.username,
            "prj_id": ObjectId(token_data.context)
        })
    elif (scope == USERTYPE_CLIENT or scope == USERTYPE_EXPERT):
        collection = get_collection(db, DOCTYPE_PROJECT)
        user = await get_project_member(db, token_data.context, token_data.username)
    else:
        collection = get_collection(db, DOCTYPE_USER)
        user = await collection.find_one({"username": token_data.username})

    user["context"] = token_data.context
    if not (scope == USERTYPE_GAIA or scope == USERTYPE_LICENSE):
        user['admin_roles'] = []
    logging.info(token_data.context)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def get_current_active_user(current_user: UserInApp = Security(get_current_user)):
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_superuser(current_user: UserInApp = Security(get_current_user)):
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


async def get_current_project_creator(current_user: UserInApp = Security(get_current_user)):
    if not crud.user.is_project_creator(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have project creator privileges"
        )
    return current_user


async def get_current_project_manager(
current_user: UserInApp = Security(get_current_user)):
    if not crud.user.is_project_manager(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have project manager privileges"
        )
    return current_user


async def get_current_project_member(
current_user: UserInApp = Security(get_current_user)):
    if not crud.user.is_project_member(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have project manager privileges"
        )
    return current_user
