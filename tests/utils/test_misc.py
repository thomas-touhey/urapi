#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Tests for :py:mod:`urapi.utils.misc`."""

from __future__ import annotations

from typing import Any

import pytest

from urapi.utils.misc import fix_validation_code


@pytest.mark.parametrize(
    "inp,outp",
    (
        ("123", "0123"),
        ("7", "0007"),
        ("00123", "0123"),
        (None, None),
        (123, 123),
    ),
)
def test_fix_validation_code(inp: Any, outp: Any) -> None:
    assert fix_validation_code(inp) == outp
