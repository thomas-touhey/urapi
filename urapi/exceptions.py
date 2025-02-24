#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Exception definition."""

from __future__ import annotations

from typing import ClassVar

from .schemas.error import ErrorType


class Error(Exception):
    """Error translatable to an error schema."""

    __slots__ = ("detail", "status", "title", "type")

    TYPE: ClassVar[ErrorType | None] = None
    """Default error type, used if no type is provided."""

    TITLE: ClassVar[str | None] = None
    """Default error title, used if no title is provided."""

    DETAIL: ClassVar[str | None] = None
    """Default error detail, used if no detail is provided."""

    STATUS: ClassVar[int] = 400
    """Default HTTP status code, used if no status code is provided."""

    detail: str
    """Error detail."""

    status: int
    """HTTP status code."""

    title: str
    """Error title."""

    type: ErrorType
    """Error type."""

    def __init__(
        self,
        /,
        *,
        type: ErrorType | None = None,
        title: str | None = None,
        detail: str | None = None,
        status: int | None = None,
    ) -> None:
        if type is None:
            type = self.TYPE
            if type is None:
                raise ValueError("Error type is missing.")

        if title is None:
            title = self.TITLE
            if title is None:
                raise ValueError("Error title is missing.")

        if detail is None:
            detail = self.DETAIL
            if detail is None:
                raise ValueError("Error detail is missing.")

        if status is None:
            status = self.STATUS

        self.type = type
        self.title = title
        self.detail = detail
        self.status = status


class NotFound(Error):
    """Resource has not been found."""

    TYPE = "urn:error:not-found"
    TITLE = "Not Found"
    DETAIL = "Resource was not found."
    STATUS = 404


class AlreadyExists(Error):
    """A resource already exists with the provided identifying data."""

    TYPE = "urn:error:already-exists"
    TITLE = "Already Exists"
    DETAIL = "A resource already exists with the provided identifying data."
    STATUS = 409


class InvalidCredentials(Error):
    """Invalid credentials."""

    TYPE = "urn:error:invalid-credentials"
    TITLE = "Invalid Credentials"
    DETAIL = "The presented credentials are invalid."
    STATUS = 401


class UserNotValidated(Error):
    """The client is trying to authenticate as a non-validated user."""

    TYPE = "urn:error:user-not-validated"
    TITLE = "User Not Validated"
    DETAIL = "The provided user has not been validated."
    STATUS = 401


class UserAlreadyValidated(Error):
    """The client is trying to validate an already validated user."""

    TYPE = "urn:error:user-already-validated"
    TITLE = "User Already Validated"
    DETAIL = "The provided user is already validated."
    STATUS = 409


class IncorrectCode(Error):
    """Code is incorrect."""

    TYPE = "urn:error:incorrect-code"
    TITLE = "Incorrect Code"
    DETAIL = "The provided code is incorrect."
    STATUS = 400


class ExpiredCode(Error):
    """Code has expired."""

    TYPE = "urn:error:expired-code"
    TITLE = "Expired Code"
    DETAIL = "The provided code has expired."
    STATUS = 400
