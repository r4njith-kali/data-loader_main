
"""Database configuration resolution for the SDM integration."""

import os
from typing import Any, Mapping, Optional

from definitions import CONFIG_DIR
from src.utils.utilities import config_param


ENV_MAPPING = {
    "host": "SDM_DB_HOST",
    "port": "SDM_DB_PORT",
    "database": "SDM_DB_NAME",
    "user": "SDM_DB_USER",
    "password": "SDM_DB_PASSWORD",
    "schema": "SDM_DB_SCHEMA",
}


def resolve_db_config(
    config: Optional[Mapping[str, Any]] = None,
) -> dict:
    """Resolve database configuration with environment overrides."""
    if config is None:
        config = config_param(
            config_file=f"{CONFIG_DIR}/sdm_config.yaml",
            field="sdm_db",
        )

    resolved = dict(config)

    for key, env_name in ENV_MAPPING.items():
        value = os.getenv(env_name)

        if value is not None:
            resolved[key] = value

    required = [
        "host",
        "port",
        "database",
        "user",
        "password",
        "schema",
    ]

    missing = [
        key for key in required
        if resolved.get(key) is None or str(resolved[key]) == ""
    ]

    if missing:
        raise ValueError(
            f"Missing database configuration: {missing}"
        )

    try:
        resolved["port"] = int(resolved["port"])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Database port must be an integer"
        ) from exc

    if not 1 <= resolved["port"] <= 65535:
        raise ValueError(
            "Database port must be between 1 and 65535"
        )

    return resolved
