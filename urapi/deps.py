#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Dependency definitions."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .auth import Auth as _Auth, get_basic_auth as _get_basic_auth
from .database import Database as _Database
from .serializer import Serializer as _Serializer
from .settings import Settings as _Settings
from .smtp import SMTP as _SMTP

_http_basic = HTTPBasic()


@lru_cache
def _get_settings() -> Settings:
    """Get settings."""
    return _Settings()


Database = Annotated[_Database, Depends(lambda: _Database(_get_settings()))]
Serializer = Annotated[_Serializer, Depends(_Serializer)]
Settings = Annotated[_Settings, Depends(_get_settings)]
SMTP = Annotated[_SMTP, Depends(lambda: _SMTP(_get_settings()))]


async def _get_auth_using_dependencies(
    credentials: Annotated[HTTPBasicCredentials, Depends(_http_basic)],
    db: Database,
) -> _Auth:
    """Get authorization.

    :param credentials: Credentials obtained from the HTTP Basic authorization.
    :param db: Database, obtained from dependency injection.
    """
    return await _get_basic_auth(credentials=credentials, db=db)


async def _get_unvalidated_auth_using_dependencies(
    credentials: Annotated[HTTPBasicCredentials, Depends(_http_basic)],
    db: Database,
) -> _Auth:
    """Get authorization, including unvalidated codes.

    :param credentials: Credentials obtained from the HTTP Basic authorization.
    :param db: Database, obtained from dependency injection.
    """
    return await _get_basic_auth(
        credentials=credentials,
        db=db,
        validated=False,
    )


Auth = Annotated[_Auth, Depends(_get_auth_using_dependencies)]
UnvalidatedAuth = Annotated[
    _Auth,
    Depends(_get_unvalidated_auth_using_dependencies),
]
