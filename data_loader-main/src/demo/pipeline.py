
"""Reproducible Industrial IoT ETL demonstration."""

import logging
import os
from datetime import datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import insert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://etl_user:local_demo_only@127.0.0.1:5433/industrial_iot",
)

metadata = MetaData()

sensor_readings = Table(
    "sensor_readings",
    metadata,
    Column("reading_id", String(100), primary_key=True),
    Column("device_id", String(50), nullable=False),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("temperature_c", Float, nullable=False),
    Column("vibration_mm_s", Float, nullable=False),
    Column("power_kw", Float, nullable=False),
    Column("quality_status", String(20), nullable=False),
)


def extract() -> pd.DataFrame:
    """Generate deterministic synthetic industrial sensor readings."""
    logger.info("Extracting synthetic industrial IoT data")

    base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    records = []

    for device_number in range(1, 6):
        device_id = f"MOTOR-{device_number:03d}"

        for hour in range(24):
            timestamp = base_time + timedelta(hours=hour)

            records.append(
                {
                    "reading_id": f"{device_id}-{hour:02d}",
                    "device_id": device_id,
                    "timestamp": timestamp,
                    "temperature_c": 40 + device_number * 2 + hour * 0.15,
                    "vibration_mm_s": 1.2 + device_number * 0.2,
                    "power_kw": 5.0 + device_number * 0.5,
                }
            )

    return pd.DataFrame(records)


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Validate, clean, and enrich incoming sensor records."""
    logger.info("Transforming %d records", len(df))

    required_columns = [
        "reading_id",
        "device_id",
        "timestamp",
        "temperature_c",
        "vibration_mm_s",
        "power_kw",
    ]

    missing_columns = set(required_columns) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    cleaned = df.copy()

    cleaned = cleaned.dropna(subset=required_columns)
    cleaned = cleaned.drop_duplicates(subset=["reading_id"])

    for column in ["temperature_c", "vibration_mm_s", "power_kw"]:
        cleaned[column] = pd.to_numeric(
            cleaned[column], errors="coerce"
        )

    cleaned["timestamp"] = pd.to_datetime(
        cleaned["timestamp"], utc=True, errors="coerce"
    )

    cleaned = cleaned.dropna(subset=required_columns)

    cleaned = cleaned[
        cleaned["temperature_c"].between(-40, 150)
        & cleaned["vibration_mm_s"].ge(0)
        & cleaned["power_kw"].ge(0)
    ].copy()

    cleaned["quality_status"] = "NORMAL"

    cleaned.loc[
        (cleaned["temperature_c"] > 80)
        | (cleaned["vibration_mm_s"] > 4.5),
        "quality_status",
    ] = "WARNING"

    logger.info("Validated %d records", len(cleaned))

    return cleaned


def load(df: pd.DataFrame, engine) -> int:
    """Load validated records with duplicate-safe inserts."""
    metadata.create_all(engine)

    records = df.to_dict(orient="records")

    if not records:
        return 0

    with engine.begin() as connection:
        statement = insert(sensor_readings).values(records)
        statement = statement.on_conflict_do_nothing(
            index_elements=["reading_id"]
        )
        result = connection.execute(statement)

    inserted = result.rowcount
    logger.info("Inserted %d new records", inserted)

    return inserted


def run_pipeline() -> None:
    """Execute the extract-transform-load workflow."""
    logger.info("Starting Industrial IoT ETL pipeline")

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    try:
        raw_data = extract()
        clean_data = transform(raw_data)
        inserted = load(clean_data, engine)

        with engine.connect() as connection:
            total = connection.scalar(
                select(func.count()).select_from(sensor_readings)
            )

        logger.info(
            "ETL completed | extracted=%d | valid=%d | inserted=%d | total=%d",
            len(raw_data),
            len(clean_data),
            inserted,
            total,
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    run_pipeline()
