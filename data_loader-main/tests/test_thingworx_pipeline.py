
"""End-to-end ThingWorx ingestion integration test."""

import os
from unittest.mock import Mock
from uuid import uuid4

from sqlalchemy import create_engine, delete, func, select

from src.demo.measurement_loader import (
    iot_measurements,
    metadata,
)
from src.demo.thingworx_pipeline import (
    ingest_thingworx_history,
)


def test_thingworx_to_postgres():
    url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg2://etl_user:local_demo_only@127.0.0.1:5433/industrial_iot",
    )

    engine = create_engine(url)
    device_id = f"TEST-MOTOR-{uuid4().hex[:12]}"

    client = Mock()

    client.post_request.side_effect = [
        {
            "rows": [
                {"timestamp": 1767225600000, "value": 45.2},
                {"timestamp": 1767225660000, "value": 45.5},
            ]
        },
        {
            "rows": [
                {"timestamp": 1767225601000, "value": 12.5},
                {"timestamp": 1767225661000, "value": 12.7},
            ]
        },
    ]

    try:
        first = ingest_thingworx_history(
            client=client,
            engine=engine,
            device_id=device_id,
            property_names=["MOTOR_TEMP", "CURRENT"],
            start_date="2026-01-01T00:00:00Z",
            end_date="2026-01-02T00:00:00Z",
        )

        client.post_request.side_effect = [
            {
                "rows": [
                    {"timestamp": 1767225600000, "value": 45.2},
                    {"timestamp": 1767225660000, "value": 45.5},
                ]
            },
            {
                "rows": [
                    {"timestamp": 1767225601000, "value": 12.5},
                    {"timestamp": 1767225661000, "value": 12.7},
                ]
            },
        ]

        second = ingest_thingworx_history(
            client=client,
            engine=engine,
            device_id=device_id,
            property_names=["MOTOR_TEMP", "CURRENT"],
            start_date="2026-01-01T00:00:00Z",
            end_date="2026-01-02T00:00:00Z",
        )

        assert first["extracted"] == 4
        assert first["inserted"] == 4
        assert second["inserted"] == 0

        with engine.connect() as connection:
            count = connection.scalar(
                select(func.count())
                .select_from(iot_measurements)
                .where(
                    iot_measurements.c.device_id == device_id
                )
            )

        assert count == 4

    finally:
        metadata.create_all(engine)

        with engine.begin() as connection:
            connection.execute(
                delete(iot_measurements).where(
                    iot_measurements.c.device_id == device_id
                )
            )

        engine.dispose()
