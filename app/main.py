from fastapi import FastAPI, Request
from starlette.exceptions import HTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from starlette.middleware.cors import CORSMiddleware
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from app.api.api_v1.api import router as api_router
from app.core import config
from app.core.errors import http_422_error_handler, http_error_handler
from app.db.mongo import close_connection, connect_to_mongo

app = FastAPI(title=config.PROJECT_NAME)

# Return a Cache-Control header for all requests.
# The no-cache directive disables caching on the zeit CDN.
# Including this better demonstrates using FastAPI as a
# serverless function.
@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache"
    return response

sentry_sdk.init(config.SENTRY_DSN)
SentryAsgiMiddleware(app)

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_connection)

# CORS
origins = []

# GPQ EV STACKS
# gpq_touch_stacks = {}

# Set all CORS enabled origins
if config.BACKEND_CORS_ORIGINS:
    origins_raw = config.BACKEND_CORS_ORIGINS.split(",")
    for origin in origins_raw:
        use_origin = origin.strip()
        origins.append(use_origin)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ),

# app.add_exception_handler(HTTPException, http_error_handler)
# app.add_exception_handler(HTTP_422_UNPROCESSABLE_ENTITY, http_422_error_handler)

# Test Sentry
@app.get('/sentry')
def test_sentry():
    rs = 1 / 0
    return 'Hello Sentry'


app.include_router(api_router, prefix=config.API_V1_STR)
