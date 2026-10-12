
"""Tests for SDM database configuration."""

import pytest

from src.utils.db_config import resolve_db_config


@pytest.fixture
def base_config():
    return {
        "host": "localhost",
        "port": 5433,
        "database": "industrial_iot",
        "user": "etl_user",
        "password": "example_password",
        "schema": "public",
    }


def test_resolves_explicit_config(base_config):
    result = resolve_db_config(base_config)

    assert result["host"] == "localhost"
    assert result["port"] == 5433


def test_environment_overrides_config(
    monkeypatch, base_config
):
    monkeypatch.setenv(
        "SDM_DB_HOST", "postgres.internal"
    )
    monkeypatch.setenv(
        "SDM_DB_PORT", "5432"
    )

    result = resolve_db_config(base_config)

    assert result["host"] == "postgres.internal"
    assert result["port"] == 5432


def test_rejects_missing_password(base_config):
    base_config["password"] = ""

    with pytest.raises(
        ValueError, match="Missing database configuration"
    ):
        resolve_db_config(base_config)


def test_rejects_invalid_port(base_config):
    base_config["port"] = "invalid"

    with pytest.raises(
        ValueError, match="port must be an integer"
    ):
        resolve_db_config(base_config)


def test_rejects_out_of_range_port(base_config):
    base_config["port"] = 70000

    with pytest.raises(
        ValueError, match="between 1 and 65535"
    ):
        resolve_db_config(base_config)
