#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""SMTP service."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from email.message import EmailMessage

from aiosmtplib import SMTP as _SMTP
from pydantic import EmailStr

from urapi.settings import Settings


class SMTP:
    """SMTP service, used to send the code."""

    __slots__ = ("settings",)

    settings: Settings
    """Settings."""

    def __init__(self, settings: Settings, /) -> None:
        self.settings = settings

    @asynccontextmanager
    async def client(self, /) -> AsyncIterator[_SMTP]:
        """Get the asynchronous SMTP client in a context."""
        smtp_url = self.settings.smtp_url

        client = _SMTP()
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

        try:
            yield client
        finally:
            await client.quit()

    async def send(self, text: str, /, *, to: EmailStr) -> None:
        """Send a plaintext e-mail.

        :param text: Plaintext message to send.
        :param to: E-mail address to which to send the plaintext e-mail.
        """
        message = EmailMessage()
        message.set_content(text)
        message["From"] = str(self.settings.smtp_from)
        message["To"] = str(to)
        message["Subject"] = "Your account validation code"

        async with self.client() as client:
            await client.send_message(message)
