#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Tests for :py:mod:`urapi.serializer`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from urapi.database.models import UserModel
from urapi.schemas.user import UserSchema, UserUnvalidatedStatusSchema
from urapi.serializer import Serializer


@pytest.fixture()
def serializer() -> Serializer:
    return Serializer()


def test_serialize_unvalidated_user(serializer: Serializer) -> None:
    now = datetime.now(UTC)
    five_minutes_ago = now - timedelta(minutes=5)

    user_model = UserModel(
        id="0288dde3-9d8e-427f-973e-684114d23fbe",
        email_address="john.doe@example.org",
        password_hash="$pbkdf2-sha256$500000$cxBds9ZOzzwcmnfeGRu9rQ$"
        + "rLZKGH1.ZUSi/wob9LJcrjDzAqjMugJREb2tYSFX9rA",
        created_at=now,
        code="1234",
        code_expires_at=five_minutes_ago,
    )

    assert serializer.serialize_user(user_model) == UserSchema(
        email_address="john.doe@example.org",
        created_at=now,
        status=UserUnvalidatedStatusSchema(),
    )
