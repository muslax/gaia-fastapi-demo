import logging
from datetime import datetime, timedelta

from bson.objectid import ObjectId
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm as OAuth2Form

from app.api.security import get_current_user
from app.core.config import (ACCESS_TOKEN_EXPIRE_MINUTES, DOCTYPE_PERSONA,
                             DOCTYPE_PROJECT, DOCTYPE_USER, USERTYPE_CLIENT,
                             USERTYPE_EXPERT, USERTYPE_GAIA, USERTYPE_LICENSE,
                             USERTYPE_PERSONA)
from app.core.jwt import create_access_token
from app.core.security import get_password_hash
from app.crud import user as crud
from app.crud.persona import authenticate_persona
from app.crud.project import authenticate_member
from app.crud.user import authenticate, authenticate_licensee
from app.crud.utils import get_collection
from app.db.mongo import AsyncIOMotorClient as DBClient
from app.db.mongo import get_database
# from app.models.context import
from app.models.msg import Msg
from app.models.token import Token, Token2
from app.models.user import User, UserWithContext
from app.utils import (generate_password_reset_token,
                       send_reset_password_email, verify_password_reset_token)

router = APIRouter()

client = Depends(get_database)

# user_stack = {}

# Type      Scope       Client_ID  (context)
# ==========================================
# Gaia	    gaia	    gaia
# License	license	    License ID
# Client	client	    Project ID
# Expert	expert	    Project ID
# Persona	persona	    Project ID

def define_scope(form_data: OAuth2Form):
    scope = ""
    if len(form_data.scopes) > 0:
        scope = form_data.scopes[0].lower()
    if scope == USERTYPE_GAIA:
        return USERTYPE_GAIA
    elif scope == USERTYPE_LICENSE:
        return USERTYPE_LICENSE
    elif scope == USERTYPE_CLIENT:
        return USERTYPE_CLIENT
    elif scope == USERTYPE_EXPERT:
        return USERTYPE_EXPERT
    elif scope ==  USERTYPE_PERSONA:
        return USERTYPE_PERSONA
    return None


@router.post("/login")  # , response_model=Token
async def jwt_login(form_data: dict, db: DBClient=client):
    """Login with form dict"""
    logging.info(f">>> {__name__}: {login.__name__}")
    user = None
    scope = form_data['scope']
    context = form_data['client_id']
    # username = form_data['username']
    # password = form_data['password']
    if not scope:
        raise HTTPException(
            status_code=400,
            detail="Could not initiate scope."
        )

    # context = form_data.client_id
    if (not scope == USERTYPE_GAIA) and (not ObjectId.is_valid(context)):
        raise HTTPException(
            status_code=400,
            detail="Invalid context"
        )

    if scope == USERTYPE_GAIA:
        # context = scope
        user = await authenticate(
            db=db,
            username=form_data['username'],
            password=form_data['password']
        )
    elif scope == USERTYPE_LICENSE:
        user = await authenticate_licensee(
            db=db,
            username=form_data['username'],
            password=form_data['password'],
            scope=scope,
            context=context
        )
    elif (scope == USERTYPE_CLIENT or scope == USERTYPE_EXPERT):
        user = await authenticate_member(
            db=db,
            username=form_data['username'],
            password=form_data['password'],
            role=scope,
            context=context
        )
    elif scope == USERTYPE_PERSONA:
        user = await authenticate_persona(
            db=db,
            username=form_data['username'],
            password=form_data['password'],
            # scope=scope,
            prj_id=context
        )


    logging.info("User scope  : " + scope)
    logging.info("User context: " + context)

    if (not user or user is None):
        logging.info("Login failed")
        raise HTTPException(
            status_code=400,
            detail="Ancorrect email, password, or context"
        )
        # return JSONResponse(
        #     status_code=400,
        #     content={
        #         "message": "Incorrect email, password, or context",
        #         "response": None
        #     }
        # )

    logging.info("Login succeeded")
    logging.info(user)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "id": str(user['_id']),
        "scope": scope,
        "context": context,
        "username": user['username'],
        "fullname": user['fullname'],
        "access_token": create_access_token(
            data = {
                "username": user['username'],
                "scope": scope,
                "context": context
            },
            expires_delta=access_token_expires
        ),
        "token_type": "bearer"
    }




# async def login(form_data: OAuth2Form=Depends(), db: DBClient=client):
@router.post("/access-token2")
async def login2(form_data: OAuth2Form=Depends(), db: DBClient=client):
    """
    OAuth2 compatible token login.
    """
    logging.info(f">>> {__name__}: {login.__name__}")
    user = None
    scope = define_scope(form_data)
    if not scope:
        raise HTTPException(
            status_code=400,
            detail="Could not initiate scope."
        )

    context = form_data.client_id
    if (not scope == USERTYPE_GAIA) and (not ObjectId.is_valid(context)):
        raise HTTPException(
            status_code=400,
            detail="Invalid context"
        )

    if scope == USERTYPE_GAIA:
        # context = scope
        user = await authenticate(
            db=db,
            username=form_data.username,
            password=form_data.password
        )
    elif scope == USERTYPE_LICENSE:
        user = await authenticate_licensee(
            db=db,
            username=form_data.username,
            password=form_data.password,
            scope=scope,
            context=context
        )
    elif (scope == USERTYPE_CLIENT or scope == USERTYPE_EXPERT):
        user = await authenticate_member(
            db=db,
            username=form_data.username,
            password=form_data.password,
            role=scope,
            context=context
        )
    elif scope == USERTYPE_PERSONA:
        user = await authenticate_persona(
            db=db,
            username=form_data.username,
            password=form_data.password,
            # scope=scope,
            prj_id=context
        )


    logging.info("User scope  : " + scope)
    logging.info("User context: " + context)

    if (not user or user is None):
        logging.info("Login failed")
        raise HTTPException(
            status_code=400,
            detail="Incorrect email, password, or context"
        )

    logging.info("Login succeeded")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
      "access_token": create_access_token(
          data = {
              "username": user['username'],
              "scope": scope,
              "context": context
          },
          expires_delta=access_token_expires
      ),
      "token_type": "bearer",
      "user": {
        "name": user['fullname'],
        "email": user['email'],
        "username": user['username'],
        "scope": scope,
        "context": context
      }
    }









# @router.post("/access-token", response_model=Token)
@router.post("/access-token")
async def login(form_data: OAuth2Form=Depends(), db: DBClient=client):
    """
    OAuth2 compatible token login.
    """
    logging.info(f">>> {__name__}: {login.__name__}")
    user = None
    scope = define_scope(form_data)
    if not scope:
        raise HTTPException(
            status_code=400,
            detail="Could not initiate scope."
        )

    context = form_data.client_id
    if (not scope == USERTYPE_GAIA) and (not ObjectId.is_valid(context)):
        raise HTTPException(
            status_code=400,
            detail="Invalid context"
        )

    if scope == USERTYPE_GAIA:
        # context = scope
        user = await authenticate(
            db=db,
            username=form_data.username,
            password=form_data.password
        )
    elif scope == USERTYPE_LICENSE:
        user = await authenticate_licensee(
            db=db,
            username=form_data.username,
            password=form_data.password,
            scope=scope,
            context=context
        )
    elif (scope == USERTYPE_CLIENT or scope == USERTYPE_EXPERT):
        user = await authenticate_member(
            db=db,
            username=form_data.username,
            password=form_data.password,
            role=scope,
            context=context
        )
    elif scope == USERTYPE_PERSONA:
        user = await authenticate_persona(
            db=db,
            username=form_data.username,
            password=form_data.password,
            # scope=scope,
            prj_id=context
        )


    logging.info("User scope  : " + scope)
    logging.info("User context: " + context)

    if (not user or user is None):
        logging.info("Login failed")
        raise HTTPException(
            status_code=400,
            detail="Incorrect email, password, or context"
        )

    # logging.info("Login succeeded")
    # access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # return {
    #     "access_token": create_access_token(
    #         data = {
    #             "username": user['username'],
    #             "scope": scope,
    #             "context": context
    #         },
    #         expires_delta=access_token_expires
    #     ),
    #     "token_type": "bearer",
    #     "user": {
    #       "name": user['fullname'],
    #       "email": user['email'],
    #       "username": user['username'],
    #       "scope": scope,
    #       "context": context
    #     }
    # }
    logging.info("Login succeeded")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
      "access_token": create_access_token(
          data = {
              "username": user['username'],
              "scope": scope,
              "context": context
          },
          expires_delta=access_token_expires
      ),
      "token_type": "bearer",
      "user": {
        "name": user['fullname'],
        "email": user['email'],
        "username": user['username'],
        "scope": scope,
        "context": context
      }
    }



@router.post("/test-token", response_model=UserWithContext)
async def test_token(current_user: UserWithContext = Depends(get_current_user)):
    """
    Test access token.
    """
    logging.info(">>> " + __name__ + ":" + test_token.__name__ )
    return current_user


@router.post("/password-recovery/{username}", response_model=Msg)
async def recover_password(username: str):
    """
    Password Recovery
    """
    logging.info(">>> " + __name__ + ":" + recover_password.__name__ )
    db = get_database()
    user = await crud.get(db, username)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )

    password_reset_token = generate_password_reset_token(username=username)
    send_reset_password_email(
        email_to=user['email'], username=username, token=password_reset_token
    )
    return {"msg": "Password recovery email sent."}


@router.post("/reset-password/", response_model=Msg)
async def reset_password(token: str = Body(...), new_password: str = Body(...)):
    """
    Reset password [NOT IMPLEMENTED YET]
    """
    logging.info(">>> " + __name__ + ":" + reset_password.__name__ )
    username = verify_password_reset_token(token)
    if not username:
        raise HTTPException(status_code=400, detail="Invalid token")

    db =  get_database()
    user = await crud.get(db, username)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )

    # NOT IMPLEMENTED YET
    # elif not crud.user.is_active(user):
    #     raise HTTPException(status_code=400, detail="Inactive user")
    # user_in = UserUpdate(name=username, password=new_password)
    # user = crud.user.update(bucket, username=username, user_in=user_in)
    logging.info("FULL NAME: " + user['full_name'])
    hashed_password = get_password_hash(password=new_password)
    collection = get_collection(db, DOCTYPE_USER)
    rs = await collection.update_one(
        {"username": username},
        {'$set': {
            'hashed_password': hashed_password,
            'modified': datetime.utcnow()
            }
        }
    )

    return {"msg": "Password updated successfully"}
