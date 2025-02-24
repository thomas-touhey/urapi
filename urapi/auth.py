#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Authentication / authorization management."""

from __future__ import annotations

from asyncio import sleep

from fastapi.security import HTTPBasicCredentials
from pydantic import BaseModel, ConfigDict

from urapi.database import Database
from urapi.database.models import UserModel
from urapi.exceptions import InvalidCredentials, NotFound, UserNotValidated


class Auth(BaseModel):
    """Authorization object."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    """Model configuration."""

    subject: UserModel
    """User as which the authorization is done."""


async def get_basic_auth(
    *,
    credentials: HTTPBasicCredentials,
    db: Database,
    validated: bool = True,
) -> Auth:
    """Get authorization from the provided credentials.

    :param credentials: Credentials to authenticate with.
    :param db: Database layer to use to get the user.
    :param validated: Whether to check whether the user was validated or not.
    :return: Authorization details.
    """
    # SECURITY: In order to avoid abuse / password bruteforcing using basic
    # auth, we need to introduce an arbitrary delay here.
    await sleep(1)

    try:
        user = await db.user.get(credentials.username)
    except NotFound as exc:
        raise InvalidCredentials() from exc

    if not user.verify_password(credentials.password):
        raise InvalidCredentials()

    if validated and user.code is not None:
        raise UserNotValidated()

    return Auth(subject=user)
