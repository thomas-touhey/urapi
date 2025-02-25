#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Tests for :py:mod:`urapi.utils.logging`."""

from __future__ import annotations

import logging

from pytest import LogCaptureFixture

from urapi.utils.logging import ECSFormatter


def test_ecs_formatter(caplog: LogCaptureFixture) -> None:
    logger = logging.getLogger(__name__)
    caplog.handler.setFormatter(ECSFormatter())

    with caplog.at_level(logging.INFO):
        logger.info("Unit has been teleported to safety.")

        try:
            raise ValueError("Landslide!")
        except ValueError:
            logger.exception("A landslide has occurred!")
