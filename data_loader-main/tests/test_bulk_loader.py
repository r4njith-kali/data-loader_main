
"""Integration tests for transactional PostgreSQL upserts."""

import os
from uuid import uuid4

import pandas as pd
import pytest
from sqlalchemy import (
    Column,
    Float,
    MetaData,
    String,
    Table,
    create_engine,
    delete,
    select,
)

from src.sdm.bulk_loader import upsert_dataframe


@pytest.fixture(scope="module")
def engine():
    url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg2://etl_user:local_demo_only@127.0.0.1:5433/industrial_iot",
    )
    db_engine = create_engine(url)
    yield db_engine
    db_engine.dispose()


@pytest.fixture
def telemetry_table(engine):
    metadata = MetaData()

    table = Table(
        "test_telemetry_upsert",
        metadata,
        Column("reading_id", String, primary_key=True),
        Column("thingworx_name", String, nullable=False),
        Column("value", Float, nullable=False),
    )

    metadata.create_all(engine)

    prefix = uuid4().hex

    yield table, prefix

    with engine.begin() as connection:
        connection.execute(
            delete(table).where(
                table.c.reading_id.like(f"{prefix}%")
            )
        )


def test_inserts_multiple_readings_for_same_equipment(
    engine, telemetry_table
):
    table, prefix = telemetry_table

    data = pd.DataFrame(
        [
            {
                "reading_id": f"{prefix}-001",
                "thingworx_name": "MOTOR-001",
                "value": 45.2,
            },
            {
                "reading_id": f"{prefix}-002",
                "thingworx_name": "MOTOR-001",
                "value": 45.5,
            },
        ]
    )

    inserted = upsert_dataframe(
        data,
        engine,
        table_name=table.name,
        schema="public",
        conflict_columns=["reading_id"],
    )

    assert inserted == 2


def test_skips_duplicate_measurements(
    engine, telemetry_table
):
    table, prefix = telemetry_table

    data = pd.DataFrame(
        [
            {
                "reading_id": f"{prefix}-001",
                "thingworx_name": "MOTOR-001",
                "value": 45.2,
            }
        ]
    )

    first = upsert_dataframe(
        data, engine, table.name, "public", ["reading_id"]
    )
    second = upsert_dataframe(
        data, engine, table.name, "public", ["reading_id"]
    )

    assert first == 1
    assert second == 0


def test_updates_existing_measurement(
    engine, telemetry_table
):
    table, prefix = telemetry_table
    reading_id = f"{prefix}-001"

    original = pd.DataFrame(
        [
            {
                "reading_id": reading_id,
                "thingworx_name": "MOTOR-001",
                "value": 45.2,
            }
        ]
    )

    updated = original.copy()
    updated["value"] = 48.7

    upsert_dataframe(
        original, engine, table.name, "public", ["reading_id"]
    )

    affected = upsert_dataframe(
        updated,
        engine,
        table.name,
        "public",
        ["reading_id"],
        update_existing=True,
    )

    with engine.connect() as connection:
        stored = connection.scalar(
            select(table.c.value).where(
                table.c.reading_id == reading_id
            )
        )

    assert affected == 1
    assert stored == 48.7


def test_rejects_null_conflict_keys(
    engine, telemetry_table
):
    table, _ = telemetry_table

    data = pd.DataFrame(
        [
            {
                "reading_id": None,
                "thingworx_name": "MOTOR-001",
                "value": 45.2,
            }
        ]
    )

    with pytest.raises(ValueError, match="cannot contain null"):
        upsert_dataframe(
            data, engine, table.name, "public", ["reading_id"]
        )
