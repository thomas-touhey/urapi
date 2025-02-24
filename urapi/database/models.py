#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Models for database interactions."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, EmailStr, Field

from urapi.utils.crypto import verify_password


class UserModel(BaseModel):
    """User model."""

    id: Annotated[UUID, Field(default_factory=uuid4)]
    """Local resource identifier."""

    email_address: EmailStr
    """E-mail address."""

    password_hash: str
    """Password hash."""

    created_at: AwareDatetime
    """Timezone-aware date and time at which the user has been created."""

    code: str | None = None
    """Code to be validated."""

    code_expires_at: AwareDatetime
    """Timezone-aware date and time at which the code expires."""

    def verify_password(self, password: str, /) -> bool:
        """Verify that the password is the provided one.

        :param password: Password to check against the user.
        :return: Whether the password is the correct one.
        """
        return verify_password(self.password_hash, password)
