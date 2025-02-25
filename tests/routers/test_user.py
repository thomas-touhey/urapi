#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2025 Thomas Touhey <thomas@touhey.fr>
# All rights reserved.
# *****************************************************************************
"""Tests for :py:mod:`urapi.routers.user`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture


@pytest.fixture(autouse=True)
def auto(mocker: MockerFixture, sleep_mock: AsyncMock) -> None:
    mocker.patch("urapi.routers.user.sleep", new=sleep_mock)


@pytest.fixture()
def now_mock(mocker: MockerFixture) -> Mock:
    datetime_mock = mocker.Mock(wraps=datetime)
    mocker.patch("urapi.routers.user.datetime", wraps=datetime_mock)
    return datetime_mock.now


@pytest.fixture()
def validation_code(mocker: MockerFixture) -> str:
    """Mock validation code building."""
    code = "0123"

    mocker.patch(
        "urapi.routers.user.build_verification_code",
        new=mocker.Mock(return_value=code),
    )
    return code


@pytest.fixture()
def incorrect_validation_code(validation_code: str) -> str:
    """Incorrect validation code, with correct validation code mocking."""
    return "0456"


def test_full_user_registration(
    client: TestClient,
    validation_code: str,
) -> None:
    response = client.post(
        "/v1/users",
        json={
            "email_address": "john.doe@example.org",
            "password": "john.password",
        },
    )
    assert response.status_code == 201
    assert response.json()["email_address"] == "john.doe@example.org"

    response = client.post(
        "/v1/users/self/validate",
        auth=("john.doe@example.org", "john.password"),
        json={"code": validation_code},
    )
    assert response.status_code == 204

    response = client.get(
        "/v1/users/self",
        auth=("john.doe@example.org", "john.password"),
    )
    assert response.status_code == 200
    assert response.json()["email_address"] == "john.doe@example.org"


def test_register_user_twice(client: TestClient) -> None:
    response = client.post(
        "/v1/users",
        json={
            "email_address": "john.doe@example.org",
            "password": "john.password",
        },
    )
    assert response.status_code == 201
    assert response.json()["email_address"] == "john.doe@example.org"

    response = client.post(
        "/v1/users",
        json={
            "email_address": "john.doe@example.org",
            "password": "john.password",
        },
    )
    assert response.status_code == 409
    assert response.json()["type"] == "urn:error:already-exists"


def test_validate_non_existing_user(client: TestClient) -> None:
    response = client.post(
        "/v1/users/self/validate",
        auth=("john.doe@example.org", "john.password"),
        json={"code": "1337"},
    )
    assert response.status_code == 401
    assert response.json()["type"] == "urn:error:invalid-credentials"


def test_validate_with_incorrect_password(
    client: TestClient,
    validation_code: str,
) -> None:
    response = client.post(
        "/v1/users",
        json={
            "email_address": "john.doe@example.org",
            "password": "john.password",
        },
    )
    assert response.status_code == 201
    assert response.json()["email_address"] == "john.doe@example.org"

    response = client.post(
        "/v1/users/self/validate",
        auth=("john.doe@example.org", "incorrect.password"),
        json={"code": validation_code},
    )
    assert response.status_code == 401
    assert response.json()["type"] == "urn:error:invalid-credentials"


def test_validate_user_twice(client: TestClient, validation_code: str) -> None:
    response = client.post(
        "/v1/users",
        json={
            "email_address": "john.doe@example.org",
            "password": "john.password",
        },
    )
    assert response.status_code == 201
    assert response.json()["email_address"] == "john.doe@example.org"

    response = client.post(
        "/v1/users/self/validate",
        auth=("john.doe@example.org", "john.password"),
        json={"code": validation_code},
    )
    assert response.status_code == 204

    response = client.post(
        "/v1/users/self/validate",
        auth=("john.doe@example.org", "john.password"),
        json={"code": validation_code},
    )
    assert response.status_code == 409
    assert response.json()["type"] == "urn:error:user-already-validated"


def test_validate_user_too_late(
    client: TestClient,
    validation_code: str,
    now_mock: Mock,
) -> None:
    response = client.post(
        "/v1/users",
        json={
            "email_address": "john.doe@example.org",
            "password": "john.password",
        },
    )
    assert response.status_code == 201
    assert response.json()["email_address"] == "john.doe@example.org"

    now_mock.return_value = datetime.now(UTC) + timedelta(minutes=2)

    response = client.post(
        "/v1/users/self/validate",
        auth=("john.doe@example.org", "john.password"),
        json={"code": validation_code},
    )
    assert response.status_code == 400
    assert response.json()["type"] == "urn:error:expired-code"


def test_validate_user_with_incorrect_code(
    client: TestClient,
    incorrect_validation_code: str,
) -> None:
    response = client.post(
        "/v1/users",
        json={
            "email_address": "john.doe@example.org",
            "password": "john.password",
        },
    )
    assert response.status_code == 201
    assert response.json()["email_address"] == "john.doe@example.org"

    now_mock.return_value = datetime.now(UTC) + timedelta(minutes=2)

    response = client.post(
        "/v1/users/self/validate",
        auth=("john.doe@example.org", "john.password"),
        json={"code": incorrect_validation_code},
    )
    assert response.status_code == 400
    assert response.json()["type"] == "urn:error:incorrect-code"


def test_access_unvalidated_user(client: TestClient) -> None:
    response = client.post(
        "/v1/users",
        json={
            "email_address": "john.doe@example.org",
            "password": "john.password",
        },
    )
    assert response.status_code == 201
    assert response.json()["email_address"] == "john.doe@example.org"

    response = client.get(
        "/v1/users/self",
        auth=("john.doe@example.org", "john.password"),
    )
    assert response.status_code == 401
    assert response.json()["type"] == "urn:error:user-not-validated"
