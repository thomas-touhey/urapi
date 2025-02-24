#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Miscellaneous utilities."""

from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import AnyUrl, UrlConstraints

SPACE_PATTERN = re.compile(r"\s+")

SmtpUrl = Annotated[
    AnyUrl,
    UrlConstraints(allowed_schemes=("smtp", "smtps"), host_required=True),
]
"""SMTP(s) URL."""


def fix_validation_code(value: Any, /) -> Any:
    """Try to fix incorrectly passed validation codes.

    This utility can be used in case the provided code, instead of being
    4 digits long, e.g. "0183", is "183", "000183", "0 183", and so on.

    :param value: Value that may be an incorrectly formatted validation code.
    :return: Possibly fixed validation code.
    """
    if not isinstance(value, str):
        return value

    return SPACE_PATTERN.sub("", value).lstrip("0").zfill(4)
