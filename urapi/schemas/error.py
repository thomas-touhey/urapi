#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""User-related routes."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

ErrorType = Annotated[
    str,
    StringConstraints(
        pattern=r"^urn:error:[a-z][a-z0-9]*(?:-[a-z][a-z0-9]*)*$",
    ),
]
"""Error type, as an URN."""


class ValidationErrorSchema(BaseModel):
    """Validation error detail.

    This is based on :py:class:`pydantic_core.ErrorDetails`, which can't be
    used directly due to TypedDict not being usable directly before
    Python 3.12.
    """

    type: str
    """Validation error type."""

    loc: list[str | int]
    """List of strings and integers identifying the error location."""

    detail: str
    """Human readable error message."""


class ErrorSchema(BaseModel):
    """Error schema, following RFC 9457 "Problem Details for HTTP APIs"."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "urn:error:something-bad-happened",
                    "title": "Something Bad Happened",
                    "detail": "Something bad happened, here are more details "
                    + "in a human-readable form.",
                },
            ],
        },
    )
    """Model configuration."""

    type: ErrorType
    """Machine-readable type for the error."""

    title: str
    """Human-readable title for the error."""

    detail: str
    """Human-readable detail for the error."""

    validation_errors: list[ValidationErrorSchema] | None = None
    """Validation errors, if relevant."""

    traceback: str | None = None
    """Traceback, if relevant."""

    correlation_id: str
    """Current correlation identifier."""
