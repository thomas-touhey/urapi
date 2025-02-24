#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Cryptographic utilities."""

from __future__ import annotations

import re
from base64 import b64decode, b64encode
from hashlib import pbkdf2_hmac
from os import urandom
from secrets import choice

HASHED_PASSWORD_PATTERN = re.compile(
    r"^\$pbkdf2-sha256\$([1-9][0-9]*)\$([A-Za-z0-9./]+)\$([A-Za-z0-9./]{43})$",
)


def build_verification_code() -> str:
    """Build a verification code for a user.

    Uses :py:func:`secrets.choice`, since :py:mod:`secrets` is made for
    generating cryptographically strong random numbers for secrets.

    :return: Randomly generated verification code.
    """
    return "".join(choice("0123456789") for _ in range(4))


def hash_password(password: str, /) -> str:
    """Hash the provided password using PBKDF2 with SHA256.

    This is equivalent to `pbkdf2_sha256`_, but implemented in-house.

    As per hashlib's documentation, "as of 2022, hundreds of thousands of
    iterations of SHA-256 are suggested"; this function uses 500k iterations
    following these recommandations.

    :param password: Password to hash.
    :return: Hashed password, wrapped in modular crypt format.

    .. _passlib.hash.pbkdf2_sha256:
        https://passlib.readthedocs.io/en/stable/lib/passlib.hash.pbkdf2_digest.html
    """
    rounds = 500000
    salt = urandom(16)
    content = pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        rounds,
    )

    encoded_salt = (
        b64encode(
            salt,
            altchars=b"./",
        )
        .decode("ascii")
        .rstrip("=")
    )
    encoded_content = (
        b64encode(
            content,
            altchars=b"./",
        )
        .decode("ascii")
        .rstrip("=")
    )
    return f"$pbkdf2-sha256${rounds}${encoded_salt}${encoded_content}"


def verify_password(password_hash: str, password: str, /) -> bool:
    """Verify the password corresponds to the password hash.

    The password hash is expected to be of modular crypt format, and using
    PBKDF2 with SHA256; password hashes made with :py:func:`hash_password`
    fit the bill.

    :param password_hash: Password hash to verify the password against.
    :param password: Password to verify.
    :return: Whether the password matches or not.
    """
    match = HASHED_PASSWORD_PATTERN.fullmatch(password_hash)
    if match is None:
        raise ValueError("Invalid password hash.")

    rounds = int(match[1])
    salt = b64decode(match[2].encode("ascii") + b"===", altchars=b"./")
    content = b64decode(match[3].encode("ascii") + b"===", altchars=b"./")

    return content == pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        rounds,
    )
