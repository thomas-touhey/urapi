#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Database-related definitions and utilities."""

from __future__ import annotations

from asyncio import Lock

from asyncpg import Connection, connect as connect_asyncpg

from urapi.settings import Settings

from .repositories import DatabaseRepositorySource, UserDatabaseRepository


class Database(DatabaseRepositorySource):
    """Database session handler."""

    __slots__ = ("connection", "connection_lock", "settings", "user")

    user: UserDatabaseRepository
    """User database repository."""

    settings: Settings
    """Settings used to connect to the database."""

    connection: Connection | None
    """Connection."""

    connection_lock: Lock
    """Lock to obtain the connection."""

    def __init__(self, settings: Settings, /) -> None:
        self.connection = None
        self.connection_lock = Lock()
        self.settings = settings

        self.user = UserDatabaseRepository(self)

    async def connect(self, /) -> Connection:
        """Obtain a connection to the database.

        :return: Connection.
        """
        async with self.connection_lock:
            if self.connection is None:
                self.connection = await connect_asyncpg(
                    str(self.settings.database_postgresql_url),
                )

            return self.connection
