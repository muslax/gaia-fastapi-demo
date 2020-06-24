import logging
from typing import Any, List

from fastapi import APIRouter, Body, Depends
from pydantic import EmailStr

from app.api import utils
from app.core import config
from app.crud import user as crud
from app.api.security import (
    get_current_user,
    get_current_active_user,
    get_current_superuser,
    get_current_project_creator
)
from app.db.mongo import AsyncIOMotorClient as DBClient
from app.db.mongo import get_database
from app.models.user import (
    ManyUsersResponse, User, UserBase, UserInDB, UserCreate, UserResponse, UserUpdate,
    UserWithContext
)


router = APIRouter()

client = Depends(get_database)


@router.get("/users", response_model=List[User])
async def read_users(
    limit: int = 50,
    skip: int=0,
    db: DBClient=client,
    current_user: UserInDB=Depends(get_current_active_user)
    ):
    logging.info(">>> " + __name__ + ":" + read_users.__name__ )
    users = await crud.get_multi(db, limit, skip)
    return users
    # return utils.create_aliased_response(
    #     ManyUsersResponse(response=users, count=len(users))
    # )


@router.post("/users/create-user", summary="Create user", response_model=User)
async def create_user(data: UserCreate, db: DBClient=client):
    """Required fields: `fullname`, `username`, `email`, `password`."""
    logging.info(">>> " + __name__ + ":" + create_user.__name__ )
    # if not (type == config.USERTYPE_GAIA or type == config.USERTYPE_LICENSE):
    #     return utils.error_400_response("Type can only be 'gaia' or 'license'")
    data = data.dict()
    data['type'] = config.USERTYPE_GAIA
    data = UserCreate(**data)

    msg = await crud.check_free_email_username(db, data.username, data.email)
    if msg:
        return utils.error_400_response(msg)

    user = await crud.create(db, data)
    if user:
        return utils.create_aliased_response(UserResponse(response=user))

    return utils.create_500_response("User creation failed")


# @router.post("/users/create-users", summary="Create users", response_model=List[Any])
# async def create_many(users: List[UserCreate], db: DBClient = client):
#     """Create many users at one batch"""
#     logging.info(">>> " + __name__ + ":" + create_many.__name__ )
#     rs = await crud.create_many(db, users)
#     if rs:
#         return rs
#     return utils.create_500_response("Operation failed")


@router.post("/users/create-license", summary="Create license", response_model=User)
async def create_license(data: UserCreate, db: DBClient=client):
    """Required fields: `fullname`, `username`, `email`, `password`."""
    logging.info(">>> " + __name__ + ":" + create_license.__name__ )
    data = data.dict()
    data['type'] = config.USERTYPE_LICENSE
    data = UserCreate(**data)

    msg = await crud.check_free_email_username(db, data.username, data.email)
    if msg:
        return utils.error_400_response(msg)

    user = await crud.create(db, data)
    if user:
        return utils.create_aliased_response(UserResponse(response=user))

    return utils.create_500_response("User creation failed")


@router.get("/users/me", response_model=UserWithContext)
async def read_user_me(current_user: UserInDB=Depends(get_current_active_user)):
    """
    Get current user.
    """
    return current_user


# @router.put("/users/me", response_model=User)
async def update_user_me(
    *,
    password: str = Body(None),
    fullname: str = Body(None),
    email: EmailStr = Body(None),
    current_user: UserInDB = Depends(get_current_active_user),
    db: DBClient=client
):
    """
    Update own user
    """
    # user_in = UserUpdate(**current_user.dict())
    user_in = UserUpdate(**current_user)
    if password is not None:
        user_in.password = password
    if fullname is not None:
        user_in.fullname = fullname
    if user_in.email is not None:
        user_in.email = email
    user = await crud.update(db, current_user["_id"], user_in)
    if user:
        return utils.create_aliased_response(UserResponse(response=user))
    return utils.create_404_response()


@router.get("/users/{username}", response_model=User)
async def read_user(username: str, db: DBClient=client):
    """Read user by id, username, or email"""
    logging.info(">>> " + __name__ + ":" + read_user.__name__ )
    user = await crud.get(db, username)
    if user:
        return utils.create_aliased_response(UserResponse(response=user))
    return utils.create_404_response()


# @router.put("/users/{ref}", response_model=User)
async def update_user(ref: str, data: UserUpdate, db: DBClient=client):
    """Update user info"""
    logging.info(">>> " + __name__ + ":" + update_user.__name__ )
    user = await crud.get(db, ref)
    if not user:
        return utils.create_404_response()

    user = await crud.update(db, user["_id"], data)
    if user:
        return utils.create_aliased_response(UserResponse(response=user))
    return utils.create_404_response()
