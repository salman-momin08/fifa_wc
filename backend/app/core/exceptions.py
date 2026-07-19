"""
Centralized Exception Handlers.

Intercepts unhandled exceptions, validation errors, and DB errors to return clean JSON responses.
"""
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import logger


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled application exceptions globally.

    Args:
        request: Incoming HTTP Request instance.
        exc: Raised Exception instance.

    Returns:
        JSONResponse with 500 status code and sanitized detail message.
    """
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred. Please contact stadium IT operations."},
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle database operational and query exceptions.

    Args:
        request: Incoming HTTP Request instance.
        exc: Raised SQLAlchemyError instance.

    Returns:
        JSONResponse with 500 status code.
    """
    logger.error(f"Database Error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database operational error occurred."},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic request body and query parameter validation failures.

    Args:
        request: Incoming HTTP Request instance.
        exc: Raised RequestValidationError instance.

    Returns:
        JSONResponse with 422 status code and validation error list.
    """
    logger.warning(f"Request Validation Failure on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )
