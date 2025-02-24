#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""User-related routes."""

from __future__ import annotations

from asyncio import sleep
from datetime import UTC, datetime
from logging import getLogger
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Body

from urapi.database.models import UserModel
from urapi.deps import (
    SMTP,
    Auth,
    Database,
    Serializer,
    Settings,
    UnvalidatedAuth,
)
from urapi.exceptions import ExpiredCode, IncorrectCode, UserAlreadyValidated
from urapi.schemas.user import (
    UserCreationPayloadSchema,
    UserSchema,
    UserValidationPayloadSchema,
)
from urapi.utils.crypto import build_verification_code

router = APIRouter(tags=["Users"])
logger = getLogger(__name__)


async def _send_code(
    *,
    user: UserModel,
    smtp: SMTP,
) -> None:
    """Send the account verification code to a user.

    :param user: User to send the account verification code to.
    :param smtp: SMTP service to use to send the code.
    """
    await smtp.send(
        f"Hello there!\n\nHere's your account verification code: {user.code}\n"
        + "\nSee you in a bit!\n",
        to=user.email_address,
    )


@router.post("/v1/users", status_code=201)
async def create_user(
    payload: Annotated[UserCreationPayloadSchema, Body()],
    db: Database,
    smtp: SMTP,
    settings: Settings,
    serializer: Serializer,
    background: BackgroundTasks,
) -> UserSchema:
    """Create a user."""
    logger.info(
        "Attempting to create user with e-mail address: %s",
        payload.email_address,
    )
    user = await db.user.create(
        email_address=payload.email_address,
        password=payload.password,
        code=build_verification_code(),
        code_expires_at=datetime.now(UTC)
        + settings.account_verification_code_validity_period,
    )

    logger.info("Creation successful, code is: %s", user.code)
    background.add_task(_send_code, user=user, smtp=smtp)

    return serializer.serialize_user(user)


@router.get("/v1/users/self")
async def get_user(
    auth: Auth,
    serializer: Serializer,
) -> UserSchema:
    """Get the current user."""
    return serializer.serialize_user(auth.subject)


@router.post("/v1/users/self/validate", status_code=204, response_model=None)
async def validate_user(
    auth: UnvalidatedAuth,
    payload: Annotated[UserValidationPayloadSchema, Body()],
    db: Database,
) -> None:
    """Validate a user."""
    code = auth.subject.code
    if code is None:
        raise UserAlreadyValidated()

    if datetime.now(UTC) >= auth.subject.code_expires_at:
        logger.warning(
            "Tried to validate expired user with e-mail address: %s",
            auth.subject.email_address,
        )
        raise ExpiredCode()

    # Sleep to prevent code bruteforcing, which would defeat the point.
    await sleep(2)

    if payload.code != code:
        logger.warning(
            "Incorrect code %s (expected: %s) for user with e-mail addr.: %s",
            payload.code,
            code,
            auth.subject.email_address,
        )
        raise IncorrectCode()

    logger.info(
        "Code is correct, validating user with e-mail address: %s",
        auth.subject.email_address,
    )
    await db.user.validate(auth.subject)
