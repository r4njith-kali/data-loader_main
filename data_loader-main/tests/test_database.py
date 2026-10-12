
"""PostgreSQL integration tests for the Industrial IoT ETL pipeline."""

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select, delete

from src.demo.pipeline import (
    extract,
    transform,
    load,
    metadata,
    sensor_readings,
)


@pytest.fixture(scope="module")
def db_engine():
    """Connect to the dedicated local PostgreSQL demo database."""
    url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg2://etl_user:local_demo_only@127.0.0.1:5433/industrial_iot",
    )

    engine = create_engine(url, pool_pre_ping=True)
    metadata.create_all(engine)

    yield engine

    engine.dispose()


@pytest.fixture
def sample_data(db_engine):
    """Create unique test records and remove them afterward."""
    df = transform(extract())
    prefix = f"TEST-{uuid4().hex[:12]}"

    df["reading_id"] = df["reading_id"].map(
        lambda value: f"{prefix}-{value}"
    )

    yield df

    ids = df["reading_id"].tolist()

    with db_engine.begin() as connection:
        connection.execute(
            delete(sensor_readings).where(
                sensor_readings.c.reading_id.in_(ids)
            )
        )


def test_database_insert(db_engine, sample_data):
    inserted = load(sample_data, db_engine)

    assert inserted == 120

    with db_engine.connect() as connection:
        count = connection.scalar(
            select(func.count())
            .select_from(sensor_readings)
            .where(
                sensor_readings.c.reading_id.in_(
                    sample_data["reading_id"].tolist()
                )
            )
        )

    assert count == 120


def test_database_idempotency(db_engine, sample_data):
    first_run = load(sample_data, db_engine)
    second_run = load(sample_data, db_engine)

    assert first_run == 120
    assert second_run == 0


def test_database_empty_input(db_engine, sample_data):
    empty = sample_data.iloc[0:0]

    assert load(empty, db_engine) == 0
