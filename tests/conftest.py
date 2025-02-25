#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Configuration and fixtures."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from unittest.mock import AsyncMock

import asyncpg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_asyncio import fixture as async_fixture
from pytest_mock import MockerFixture
from pytest_postgresql.executor_noop import NoopExecutor
from pytest_postgresql.factories import (
    postgresql_noproc as postgresql_noproc_factory,
)
from pytest_postgresql.janitor import DatabaseJanitor

from urapi.asgi import app as _app


async def load_database(
    *,
    host: str,
    port: str,
    user: str,
    password: str,
    dbname: str,
) -> None:
    """Initialize the database for all tests.

    This allows creating the initial database only once, then copying its
    initial state for later tests.

    For now, this function only creates the tables according to the models.

    :param host: The host.
    :param port: The port.
    :param user: The username.
    :param password: The password.
    :param dbname: The name of the database.
    """
    conn = await asyncpg.connect(
        f"postgresql://{user}:{password}@{host}:{port}/{dbname}",
    )

    await conn.execute('DROP TABLE IF EXISTS "user"')
    await conn.execute(
        'CREATE TABLE "user" (id UUID PRIMARY KEY, '
        + "email_address TEXT UNIQUE NOT NULL, "
        + "password_hash TEXT NOT NULL, "
        + "created_at TIMESTAMP NOT NULL, code TEXT, "
        + "code_expires_at TIMESTAMP NOT NULL)",
    )


postgresql_noproc = postgresql_noproc_factory(
    host="localhost",
    user="postgres",
    password="postgres",
    dbname="urapi_tests",
    load=[lambda **kwargs: asyncio.run(load_database(**kwargs))],
)


@pytest.fixture()
def postgresql(
    mocker: MockerFixture,
    postgresql_noproc: NoopExecutor,
) -> Iterator[None]:
    """Set up PostgreSQL and the related environment for the app."""
    with DatabaseJanitor(
        user=postgresql_noproc.user,
        password=postgresql_noproc.password,
        host=postgresql_noproc.host,
        port=postgresql_noproc.port,
        version=postgresql_noproc.version,
        dbname=postgresql_noproc.dbname,
        template_dbname=postgresql_noproc.template_dbname,
    ):
        mocker.patch.dict("os.environ")
        os.environ["DATABASE_POSTGRESQL_URL"] = (
            f"postgresql://{postgresql_noproc.user}:"
            + f"{postgresql_noproc.password}@{postgresql_noproc.host}"
            + f":{postgresql_noproc.port}/{postgresql_noproc.dbname}"
        )

        yield


@pytest.fixture()
def smtp(mocker: MockerFixture) -> None:
    """Mock SMTP interactions."""
    mocker.patch.dict("os.environ")
    os.environ["SMTP_FROM"] = "from@example.org"
    os.environ["SMTP_URL"] = "smtp://smtp.example"

    from urapi.smtp import SMTP

    mocker.patch.object(
        SMTP,
        "send",
        new=mocker.AsyncMock(return_value=None),
    )


@pytest.fixture()
def sleep_mock(mocker: MockerFixture) -> AsyncMock:
    """Fixture for replacing :py:func:`asyncio.sleep`."""
    sleep_mock = mocker.AsyncMock()
    mocker.patch("urapi.auth.sleep", new=sleep_mock)
    return sleep_mock


@async_fixture()
async def app(
    mocker: MockerFixture,
    postgresql: None,
    smtp: None,
    sleep_mock: AsyncMock,
) -> AsyncIterator[FastAPI]:
    """Get the application."""
    yield _app


@pytest.fixture()
def client(app: FastAPI) -> Iterator[TestClient]:
    """Get the test client for the ASGI application."""
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
