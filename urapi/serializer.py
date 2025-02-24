#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Serializer."""

from __future__ import annotations

from datetime import UTC, datetime

from .database.models import UserModel
from .schemas.user import (
    UserAwaitingValidationStatusSchema,
    UserSchema,
    UserStatusSchema,
    UserUnvalidatedStatusSchema,
    UserValidatedStatusSchema,
)


class Serializer:
    """Serializer from database models to API schemas."""

    __slots__ = ()

    def serialize_user_status(self, user: UserModel, /) -> UserStatusSchema:
        """Serialize a user's status.

        :param user: User model instance.
        :return: Serialized user status.
        """
        if user.code is None:
            return UserValidatedStatusSchema()

        if datetime.now(UTC) >= user.code_expires_at:
            return UserUnvalidatedStatusSchema()

        return UserAwaitingValidationStatusSchema(
            expires_at=user.code_expires_at,
        )

    def serialize_user(self, user: UserModel, /) -> UserSchema:
        """Serialize a user.

        :param user: User model instance.
        :return: Serialized user.
        """
        return UserSchema(
            email_address=user.email_address,
            created_at=user.created_at,
            status=self.serialize_user_status(user),
        )
