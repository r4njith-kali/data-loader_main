
"""Reproducible industrial IoT ETL demonstration."""

import logging
import os
from datetime import datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def extract() -> pd.DataFrame:
    """Generate deterministic synthetic sensor measurements."""
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    records = []

    for hour in range(24):
        for sensor_id in ["MOTOR_001", "MOTOR_002", "HVAC_001"]:
            records.append({
                "sensor_id": sensor_id,
                "timestamp": start + timedelta(hours=hour),
                "temperature_c": 25.0 + hour * 0.3,
                "power_kw": 4.5 + hour * 0.1,
            })

    df = pd.DataFrame(records)
    logger.info("Extracted %s synthetic sensor records", len(df))
    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and transform sensor measurements."""
    required = {
        "sensor_id",
        "timestamp",
        "temperature_c",
        "power_kw",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    cleaned = df.copy()
    cleaned["timestamp"] = pd.to_datetime(
        cleaned["timestamp"], utc=True, errors="coerce"
    )
    cleaned["temperature_c"] = pd.to_numeric(
        cleaned["temperature_c"], errors="coerce"
    )
    cleaned["power_kw"] = pd.to_numeric(
        cleaned["power_kw"], errors="coerce"
    )

    cleaned = cleaned.dropna(subset=list(required))
    cleaned = cleaned.drop_duplicates(
        subset=["sensor_id", "timestamp"]
    )

    cleaned = cleaned[
        cleaned["temperature_c"].between(-40, 150)
        & (cleaned["power_kw"] >= 0)
    ].copy()

    logger.info("Validated %s sensor records", len(cleaned))
    return cleaned


def load(df: pd.DataFrame, engine) -> int:
    """Load records into PostgreSQL without inserting duplicates."""
    create_table = text("""
        CREATE TABLE IF NOT EXISTS sensor_measurements (
            sensor_id TEXT NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL,
            temperature_c DOUBLE PRECISION NOT NULL,
            power_kw DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (sensor_id, timestamp)
        )
    """)

    insert_record = text("""
        INSERT INTO sensor_measurements
            (sensor_id, timestamp, temperature_c, power_kw)
        VALUES
            (:sensor_id, :timestamp, :temperature_c, :power_kw)
        ON CONFLICT (sensor_id, timestamp) DO NOTHING
    """)

    records = df.to_dict(orient="records")

    with engine.begin() as connection:
        connection.execute(create_table)
        result = connection.execute(insert_record, records) if records else None

    inserted = result.rowcount if result is not None else 0
    logger.info("Inserted %s new records", inserted)
    return inserted


def main() -> None:
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://etl_user:local_demo_only@127.0.0.1:5433/industrial_iot",
    )

    engine = create_engine(database_url, pool_pre_ping=True)

    try:
        logger.info("Starting Industrial IoT ETL pipeline")
        raw_data = extract()
        clean_data = transform(raw_data)
        inserted = load(clean_data, engine)
        logger.info("Pipeline completed: %s records inserted", inserted)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
