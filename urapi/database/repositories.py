#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Database repository definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from asyncpg import Connection
from asyncpg.exceptions import UniqueViolationError

from urapi.exceptions import AlreadyExists, NotFound
from urapi.utils.crypto import hash_password

from .models import UserModel


class DatabaseRepositorySource:
    """Source for a database repository."""

    @abstractmethod
    async def connect(self, /) -> Connection:
        """Obtain a connection to the database.

        :return: Connection.
        """


class DatabaseRepository(ABC):
    """Database repository."""

    __slots__ = ("source",)

    source: DatabaseRepositorySource
    """Source for the database repository."""

    def __init__(self, source: DatabaseRepositorySource, /) -> None:
        self.source = source


class UserDatabaseRepository(DatabaseRepository):
    """User database repository."""

    async def get(self, email_address: str, /) -> UserModel:
        """Get details regarding a user.

        :param email_address: E-mail address of the user to get.
        :return: User.
        :raises NotFound: No user exists with that e-mail address.
        """
        conn = await self.source.connect()
        stmt = await conn.prepare(
            'SELECT "user".id, "user".email_address, "user".password_hash, '
            + '"user".created_at, "user".code, "user".code_expires_at '
            + 'FROM "user" WHERE email_address = $1 LIMIT 1',
        )

        for row in await stmt.fetch(email_address):
            return UserModel(
                id=row[0],
                email_address=row[1],
                password_hash=row[2],
                created_at=row[3].replace(tzinfo=UTC),
                code=row[4],
                code_expires_at=row[5].replace(tzinfo=UTC),
            )

        raise NotFound()

    async def create(
        self,
        /,
        *,
        email_address: str,
        password: str,
        code: str,
        code_expires_at: datetime,
    ) -> UserModel:
        """Create a user.

        :param email_address: E-mail address for the user.
        :param password: Password for the user.
        :param code: Code for the user.
        :param code_expires_at: Date and time of expiration for the code.
        :return: Created user.
        :raises AlreadyExists: A user already exists with that e-mail address.
        """
        conn = await self.source.connect()
        stmt = await conn.prepare(
            'INSERT INTO "user"(id, email_address, password_hash, created_at, '
            + "code, code_expires_at) VALUES (gen_random_uuid(), $1, $2, $3, "
            + "$4, $5) RETURNING id, email_address, password_hash, "
            + "created_at, code, code_expires_at",
        )

        if code_expires_at.tzinfo:
            code_expires_at = code_expires_at.astimezone(UTC).replace(
                tzinfo=None,
            )

        try:
            for row in await stmt.fetch(
                email_address,
                hash_password(password),
                datetime.now(UTC).replace(tzinfo=None),
                code,
                code_expires_at,
            ):
                return UserModel(
                    id=row[0],
                    email_address=row[1],
                    password_hash=row[2],
                    created_at=row[3].replace(tzinfo=UTC),
                    code=row[4],
                    code_expires_at=row[5].replace(tzinfo=UTC),
                )
        except UniqueViolationError as exc:
            raise AlreadyExists() from exc

        # We shouldn't reach this point, however universe never ceases to
        # surprise us!
        raise NotImplementedError()  # pragma: no cover

    async def validate(self, user: UserModel, /) -> None:
        """Validate a user.

        :param user: User to validate.
        """
        conn = await self.source.connect()
        stmt = await conn.prepare(
            'UPDATE "user" SET code = NULL WHERE id = $1',
        )

        await stmt.fetch(str(user.id))
        user.code = None
