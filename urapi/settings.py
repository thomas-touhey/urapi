#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Settings definition."""

from __future__ import annotations

from datetime import timedelta

from pydantic import EmailStr, PostgresDsn
from pydantic_settings import BaseSettings

from urapi.utils.misc import SmtpUrl


class Settings(BaseSettings):
    """Settings for urapi."""

    account_verification_code_validity_period: timedelta = timedelta(minutes=1)
    """Duration during which the verification code for an account is active."""

    database_postgresql_url: PostgresDsn
    """URL to the PostgreSQL database."""

    smtp_from: EmailStr
    """E-mail address from which to send e-mails."""

    smtp_url: SmtpUrl
    """URL to the SMTP server to use to send validation codes."""
