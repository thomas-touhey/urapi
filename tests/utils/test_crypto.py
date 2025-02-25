#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Tests for :py:mod:`urapi.utils.crypto`."""

from __future__ import annotations

import pytest

from urapi.utils.crypto import verify_password


def test_verify_invalid_password_hash() -> None:
    with pytest.raises(ValueError):
        verify_password("hello yes i am invalid", "anything")
