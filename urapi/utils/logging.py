#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Logging utilities."""

from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar, Token as ContextToken
from logging import (
    Formatter,
    LogRecord,
    getLogRecordFactory,
    setLogRecordFactory,
)
from socket import gethostname
from sys import exc_info as sys_exc_info
from time import gmtime
from traceback import format_tb
from typing import Any
from uuid import uuid4

from pydantic import BaseModel
from pydantic_core import to_json
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class LoggingContext(BaseModel):
    """Logging context definition."""

    correlation_id: str | None = None
    """Current correlation identifier."""


_logging_context_var: ContextVar[LoggingContext | None] = ContextVar(
    "_logging_context_var",
    default=None,
)


def get_logging_context() -> LoggingContext:
    """Get the current logging context.

    :return: Current logging context.
    """
    return _logging_context_var.get() or LoggingContext()


def make_log_record(
    *,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    original_factory: Callable[..., LogRecord],
) -> LogRecord:
    """Make a log record with contextual information.

    :param args: The positional arguments to the factory.
    :param kwargs: The keyword arguments to the factory.
    :param original_factory: The original factory to call first.
    :return: The log record to pass to the handlers.
    """
    record = original_factory(*args, **kwargs)

    # Evaluate the record message if there still are args.
    record.msg = record.getMessage()
    record.args = ()

    # Add information based on the current context.
    ctx = get_logging_context()
    if ctx.correlation_id is not None:
        record.__dict__["correlation_id"] = ctx.correlation_id

    return record


class LoggingContextMiddleware(BaseHTTPMiddleware):
    """Middleware to set up a logging context."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

        # We want to set the log factory to set request information on every
        # log produced in the context of the request, even with loggers
        # produced using ``logging.getLogger`` prior to the instantiation of
        # the logging middleware.
        original_factory = getLogRecordFactory()
        setLogRecordFactory(
            lambda *args, **kwargs: make_log_record(
                args=args,
                kwargs=kwargs,
                original_factory=original_factory,
            ),
        )

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Dispatch the request.

        :param request: The request to dispatch.
        :param call_next: The ASGI app to call next.
        :return: The next request.
        """
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:  # None or empty header.
            correlation_id = str(uuid4())

        ctx = LoggingContext(correlation_id=correlation_id)

        # The exception handler is called out of the logging context, we
        # actually want to provide it with the context as well, through
        # the request state.
        request.state.logging_context = ctx

        token: ContextToken = _logging_context_var.set(ctx)
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            _logging_context_var.reset(token)


def _remove_nones_and_empty_dicts(obj: dict[str, Any], /) -> None:
    """Remove None references and empty dictionaries in-place, recursively.

    This is used to clean ECS data in :py:class:`ECSLogFormatter`.

    :param obj: Dictionary to clean, in-place.
    """
    for value in obj.values():
        if isinstance(value, dict):
            _remove_nones_and_empty_dicts(value)

    for key in tuple(
        key for key, value in obj.items() if value is None or value == {}
    ):
        del obj[key]


class ECSFormatter(Formatter):
    """Custom formatter for JSON logs compatible with ECS.

    ECS in that context refers to Elastic Common Schema (ECS), a schema that
    can be common between applications to use utilities such as
    Application Performance Monitoring (APM).
    """

    converter = gmtime
    hostname: str

    def __init__(self, *args, **kwargs) -> None:
        # Provided parameters are ignored, in favour of overridden parameters.
        super().__init__(datefmt="%Y-%m-%dT%H:%M:%S")
        self.hostname = gethostname()

    def format(self, record: LogRecord) -> str:
        """Format a record using ECS.

        :param record: Record to format.
        :return: Formatted record.
        """
        message = record.getMessage()
        timestamp = f"{self.formatTime(record)}.{int(record.msecs):03d}Z"
        data: dict[str, Any] = {
            "@timestamp": timestamp,
            "ecs.version": "8.17.0",
            "error": {},
            "host": {"hostname": self.hostname},
            "http": {
                "request": {
                    "id": getattr(record, "correlation_id", None),
                },
            },
            "log": {
                "level": record.levelname.casefold(),
                "origin": {
                    "function": getattr(record, "funcName", None),
                    "file": {
                        "line": getattr(record, "lineno", None),
                        "name": getattr(record, "filename", None),
                    },
                },
            },
            "message": message,
        }

        exc_info = (
            sys_exc_info()
            if isinstance(record.exc_info, bool) and record.exc_info
            else record.exc_info
        )
        if exc_info and isinstance(exc_info, list | tuple):
            if record.exc_info and record.exc_info[2]:
                stack_trace = "".join(format_tb(exc_info[2]))
            elif record.stack_info:  # pragma: no cover
                stack_trace = str(record.stack_info)
            else:  # pragma: no cover
                stack_trace = None

            data["error"] = {
                "type": (
                    exc_info[0].__name__ if exc_info[0] is not None else None
                ),
                "message": str(exc_info[1]),
                "stack_trace": stack_trace,
            }

        _remove_nones_and_empty_dicts(data)
        return to_json(data).decode("utf-8")
