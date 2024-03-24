import os
import time
import uuid
from datetime import datetime

import jwt
import sentry_sdk
import structlog
import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.context import correlation_id
from fastapi import FastAPI, Response
from fastapi_jwt_auth.auth_jwt import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from pydantic import parse_obj_as
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api import api
from app.core.config import auth_jwt_settings, env_with_secrets, settings
from app.core.docs_config import set_custom_openapi
from app.core.log_config import setup_logging
from app.core.mongo_config import MongoConfig
from app.db.mongo_client import ZuMongoClient

app = FastAPI(title=settings.PROJECT_NAME, description=settings.PROJECT_DESCRIPTION)

LOG_JSON_FORMAT = parse_obj_as(bool, os.getenv("LOG_JSON_FORMAT", False))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
setup_logging(json_logs=LOG_JSON_FORMAT, log_level=LOG_LEVEL)
access_logger = structlog.stdlib.get_logger("api.access")
error_logger = structlog.get_logger("api.error")
default_logger = structlog.get_logger("default")

set_custom_openapi(app)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if "SENTRY_DNS" in env_with_secrets:
    try:
        sentry_sdk.init(
            dsn=env_with_secrets["SENTRY_DNS"],
            enable_tracing=True,
            traces_sample_rate=0.5,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                FastApiIntegration(transaction_style="endpoint"),
            ],
        )
    except Exception as e:
        print(f"Problem Setting Up Sentry => {str(e)}")


@app.get("/ping")
async def ping():
    return {"ping": "pong"}


@app.middleware("http")
async def log_incoming_request(request: Request, call_next):
    id = uuid.uuid4()
    start_time = datetime.utcnow()
    request.state.request_id = str(id)
    response = await call_next(request)
    process_time = datetime.utcnow() - start_time
    if request.url.path != "/ping":
        default_logger.info(
            "Request completed",
            extra={
                "request_id": str(id),
                "response_time_in_milliseconds": process_time.microseconds
                / 1000,  # noqa E501
                "status_code": response.status_code,
                "request_path": request.url.path,
            },
        )
    return response


app.include_router(api.api_router)


@app.on_event("startup")
async def startup():
    await ZuMongoClient.open_mongo_client()
    await ZuMongoClient.open_database(MongoConfig.MONGO_PROD_DATABASE)


@app.on_event("shutdown")
async def shutdown():
    await ZuMongoClient.close_mongo_client()


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException) -> JSONResponse:
    request_id = request.headers.get("x-request-id")
    error_logger.exception(
        f"An unhandled authjwt exception occurred {str(exc)} {exc.message}",  # type: ignore
        exc_info=True,
        http={
            "url": str(request.get("url", "")),
            "path": str(request.get("path", "")),
            "method": request.get("method", ""),
            "type": request.get("type", ""),
            "request_id": request_id,
        },
        token=request.headers.get("Authorization"),
    )
    return JSONResponse(
        status_code=exc.status_code,  # type: ignore
        content={
            "detail": exc.message,  # type: ignore
        },
    )


@app.exception_handler(ValueError)
async def value_error_exception_handler(
    request: Request, exc: ValueError
) -> JSONResponse:
    request_id = request.headers.get("x-request-id")
    error_logger.exception(
        f"An unhandled exception occurred {str(exc)}",
        exc_info=True,
        http={
            "url": str(request.get("url", "")),
            "path": str(request.get("path", "")),
            "method": request.get("method", ""),
            "type": request.get("type", ""),
            "request_id": request_id,
        },
    )
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )


@app.middleware("http")
async def logging_middleware(request: Request, call_next) -> Response:
    start_time_ns = time.perf_counter_ns()
    structlog.contextvars.clear_contextvars()

    request_id = correlation_id.get()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    # Parse the authorization header and add uuid to log if it exists
    auth_header = request.headers.get("Authorization")
    uuid = ""
    if auth_header:
        parts = auth_header.split(" ")
        try:
            payload = jwt.decode(parts[1], options={"verify_signature": False})
            uuid = payload.get("sub")
        except Exception as e:
            error_logger.exception(f"Failed to parse authorization header: {str(e)}")
    structlog.contextvars.bind_contextvars(uuid=uuid)
    structlog.contextvars.bind_contextvars(path=str(request.url.path))

    response = await call_next(request)

    if request.url.path == "/ping":
        return response

    process_time_s = (time.perf_counter_ns() - start_time_ns) / 10**9
    response.headers["X-Process-Time"] = str(process_time_s)

    client = request.client or ("Unknown", 0)
    http_version = request.scope["http_version"]
    log_data = {
        "request_id": request_id,
        "method": request.method,
        "status_code": response.status_code,
        "elapsed_time": process_time_s,
    }

    access_logger.info(
        f'{client[0]}:{client[1]} - "{request.method} {request.url.path} HTTP/{http_version}" {response.status_code}',
        **log_data,
    )

    if process_time_s > 0.5:
        access_logger.warning("Slow request", **log_data)

    return response


@app.exception_handler(Exception)
async def catch_all_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("x-request-id")
    error_logger.exception(
        f"An unhandled exception occurred {str(exc)}",
        exc_info=True,
        http={
            "url": str(request.url),
            "method": request.method,
            "request_id": request_id,
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            "message": "Something went wrong, please try again later.",
            "error_code": "500_INTERNAL_SERVER_ERROR",
            "request_id": request_id,
        },
    )


app.add_middleware(CorrelationIdMiddleware)


@AuthJWT.load_config
def get_config():
    return auth_jwt_settings


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=4522,
        log_level="info",
        reload=True,
        workers=1,  # noqa E501
    )
