#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""User-related routes."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    EmailStr,
    StringConstraints,
)

from urapi.utils.misc import fix_validation_code

ValidationCode = Annotated[str, StringConstraints(pattern=r"^[0-9]{4}$")]
"""Validation code."""


class UserAwaitingValidationStatusSchema(BaseModel):
    """Awaiting validation status schema for users."""

    type: Literal["awaiting_validation"] = "awaiting_validation"
    """Status type."""

    expires_at: AwareDatetime
    """Date and time of expiration for the status."""


class UserValidatedStatusSchema(BaseModel):
    """Validated status schema for users."""

    type: Literal["validated"] = "validated"
    """Status type."""


class UserUnvalidatedStatusSchema(BaseModel):
    """Unvalidated status schema for users."""

    type: Literal["unvalidated"] = "unvalidated"
    """Status type."""


UserStatusSchema = (
    UserAwaitingValidationStatusSchema
    | UserValidatedStatusSchema
    | UserUnvalidatedStatusSchema
)
"""User status schema, as a union type."""


class UserSchema(BaseModel):
    """User schema."""

    email_address: EmailStr
    """E-mail address for the user."""

    created_at: AwareDatetime
    """Date and time at which the user has been created."""

    status: UserStatusSchema
    """User status."""


class UserCreationPayloadSchema(BaseModel):
    """User creation payload."""

    email_address: EmailStr
    """E-mail address to assign to the new user."""

    password: Annotated[str, StringConstraints(min_length=1)]
    """Password to assign to the new user."""


class UserValidationPayloadSchema(BaseModel):
    """User validation payload."""

    code: Annotated[ValidationCode, BeforeValidator(fix_validation_code)]
    """Code sent on another medium."""
