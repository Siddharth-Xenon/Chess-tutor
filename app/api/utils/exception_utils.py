import logging

from fastapi.exceptions import HTTPException
from starlette import status

logger = logging.getLogger(__name__)


def log_exception(log_message: str, request_id: str, log_exception: str):

    logger.error(
        log_message,
        extra={"request_id": request_id, "exception": log_exception},
    )


def log_and_raise_exception(
    log_message: str,
    request_id: str,
    log_exception: str,
    user_err_message: str = "Oh Oh! An error occurred!",
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    raise_exception=True,
):

    logger.error(
        log_message,
        extra={"request_id": request_id, "exception": log_exception},
    )
    if raise_exception:
        raise HTTPException(
            status_code=status_code,
            detail=user_err_message,
        )


def raise_exception(
    user_err_message: str,
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
):
    raise HTTPException(
        status_code=status_code,
        detail=user_err_message,
    )
