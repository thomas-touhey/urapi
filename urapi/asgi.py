#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""urapi is an API for registering users."""

from __future__ import annotations

from traceback import format_exception

from fastapi import FastAPI as FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException

from .exceptions import Error
from .routers.user import router as user_router
from .schemas.error import ErrorSchema, ValidationErrorSchema
from .utils.logging import LoggingContextMiddleware

app = FastAPI(
    title="urapi",
    description="Your API for user registration!",
    responses={
        "4XX": {
            "description": "An error was present in the HTTP request.",
            "model": ErrorSchema,
        },
        "5XX": {
            "description": "The server is unable to perform the requested "
            + "operation.",
            "model": ErrorSchema,
        },
    },
    default_response_class=ORJSONResponse,
)
app.add_middleware(LoggingContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(user_router)


@app.exception_handler(Exception)
@app.exception_handler(HTTPException)
@app.exception_handler(RequestValidationError)
def handle_exception(request: Request, exc: Exception) -> Response:
    """Handle generic exceptions."""
    status = 500
    correlation_id = request.state.logging_context.correlation_id
    if isinstance(exc, Error):
        data = ErrorSchema(
            type=exc.type,
            title=exc.title,
            detail=exc.detail,
            correlation_id=correlation_id,
        )
        status = exc.status
    elif isinstance(exc, HTTPException):
        data = ErrorSchema(
            type="urn:error:generic",
            title="Generic HTTP error",
            detail=f"{exc.detail} ({exc.status_code})",
            correlation_id=correlation_id,
        )
        status = exc.status_code
    elif isinstance(exc, RequestValidationError):
        data = ErrorSchema(
            type="urn:error:invalid-request",
            title="Invalid Request",
            detail="Validation errors have occurred within the input.",
            validation_errors=[
                ValidationErrorSchema(
                    type=error["type"],
                    loc=[*error["loc"]],
                    detail=error["msg"],
                )
                for error in exc.errors()
            ],
            correlation_id=correlation_id,
        )
        status = 400
    elif isinstance(exc, NotImplementedError):
        data = ErrorSchema(
            type="urn:error:not-implemented",
            title="Not Implemented",
            detail=str(exc)
            or "The provided endpoint or feature was not implemented.",
            correlation_id=correlation_id,
        )
    else:
        exc_message = str(exc)
        if exc_message:
            exc_message = f": {exc_message}"

        data = ErrorSchema(
            type="urn:error:generic",
            title="Generic Error",
            detail=f"{exc.__class__.__name__}{exc_message}",
            traceback="\n".join(format_exception(exc)),
            correlation_id=correlation_id,
        )

    return request.app.router.default_response_class(
        jsonable_encoder(data, exclude_defaults=True),
        headers={
            "X-Correlation-ID": request.state.logging_context.correlation_id,
        },
        status_code=status,
    )
