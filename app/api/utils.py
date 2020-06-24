from pydantic import BaseModel
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def raise_not_manager():
    raise HTTPException(
        status_code=400,
        detail="The user is not the manager of this project"
    )


def raise_not_member():
    raise HTTPException(
        status_code=400,
        detail="The user is NOT a member of this project"
    )


def create_aliased_response(model: BaseModel) -> JSONResponse:
    return JSONResponse(content=jsonable_encoder(model, by_alias=True))


def error_400_response(message: str = "Bad request"):
    return JSONResponse(
        status_code=400,
        content={
            "error": message,
            "response": None
        }
    )


def create_404_response(message: str = "Not found"):
    return JSONResponse(
        status_code=404,
        content={
            "error": message,
            "response": None
        }
    )


def create_422_response(message: str = "Unprocessable entity"):
    return JSONResponse(
        status_code=422,
        content={
            "error": message,
            "response": None
        }
    )


def create_500_response(message: str = "Internal server error"):
    return JSONResponse(
        status_code=500,
        content={
            "error": message,
            "response": None
        }
    )
