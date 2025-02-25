#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Tests for :py:mod:`urapi.exceptions`."""

from __future__ import annotations

import pytest

from urapi.exceptions import Error


def test_error_with_missing_type() -> None:
    with pytest.raises(ValueError, match=r"Error type is missing"):
        Error()


def test_error_with_missing_title() -> None:
    with pytest.raises(ValueError, match=r"Error title is missing"):
        Error(type="urn:error:example")


def test_error_with_missing_detail() -> None:
    with pytest.raises(ValueError, match=r"Error detail is missing"):
        Error(type="urn:error:example", title="Example Error")
