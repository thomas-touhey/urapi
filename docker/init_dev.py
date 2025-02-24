#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Initialization script for setting up a Docker development environment.

This script ensures that all services are up, and sets up what needs setting
up.
"""

from __future__ import annotations

import asyncio
import socket
from logging import getLogger
from logging.config import fileConfig
from os import environ
from pathlib import Path

import aiosmtplib
import asyncpg
from asyncpg.exceptions import CannotConnectNowError
from pydantic import PostgresDsn, TypeAdapter

from urapi.utils.misc import SmtpUrl

logger = getLogger(__name__)


async def initialize_database() -> None:
    """Initialize the database."""
    postgres_url = TypeAdapter(PostgresDsn).validate_python(
        environ["DATABASE_POSTGRESQL_URL"],
    )

    while True:
        try:
            conn = await asyncpg.connect(str(postgres_url))
            await conn.execute('DROP TABLE IF EXISTS "user"')
            await conn.execute(
                'CREATE TABLE "user" (id UUID PRIMARY KEY, '
                + "email_address TEXT UNIQUE NOT NULL, "
                + "password_hash TEXT NOT NULL, "
                + "created_at TIMESTAMP NOT NULL, code TEXT, "
                + "code_expires_at TIMESTAMP NOT NULL)",
            )
        except (ConnectionError, CannotConnectNowError, socket.gaierror):
            logger.warning(
                "Could not connect to PostgreSQL, retrying in 250ms.",
            )
            await asyncio.sleep(0.25)
            continue
        else:
            break


async def initialize_smtp() -> None:
    """Initialize SMTP."""
    smtp_url = TypeAdapter(SmtpUrl).validate_python(environ["SMTP_URL"])

    client = aiosmtplib.SMTP()

    while True:
        try:
            await client.connect(
                hostname=smtp_url.host,
                port=(
                    smtp_url.port
                    if smtp_url.port is not None
                    else 465
                    if smtp_url.scheme == "smtps"
                    else 25
                ),
                use_tls=smtp_url.scheme == "smtps",
                username=smtp_url.username or None,
                password=smtp_url.password or None,
            )
        except (ConnectionError, socket.gaierror):
            logger.warning(
                "Could not connect to the SMTP server, retrying in 250ms.",
            )
            await asyncio.sleep(0.25)
            continue
        else:
            await client.quit()
            break


async def initialize() -> None:
    """Initialize all services."""
    await asyncio.gather(
        initialize_database(),
        initialize_smtp(),
    )


if __name__ == "__main__":
    fileConfig(Path(__file__).parent / "logging.dev.ini")
    asyncio.run(initialize())
