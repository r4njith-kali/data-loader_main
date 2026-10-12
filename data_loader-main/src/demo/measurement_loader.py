
"""PostgreSQL storage for industrial IoT measurements."""

import pandas as pd
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    MetaData,
    String,
    Table,
)
from sqlalchemy.dialects.postgresql import insert

metadata = MetaData()

iot_measurements = Table(
    "iot_measurements",
    metadata,
    Column("reading_id", String(64), primary_key=True),
    Column("device_id", String(100), nullable=False),
    Column("property_name", String(100), nullable=False),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("value", Float, nullable=False),
)


def load_measurements(df: pd.DataFrame, engine) -> int:
    """Insert new measurements without duplicating existing readings."""
    required = {
        "reading_id",
        "device_id",
        "property_name",
        "timestamp",
        "value",
    }

    if not required.issubset(df.columns):
        raise ValueError(
            f"Missing columns: {sorted(required - set(df.columns))}"
        )

    metadata.create_all(engine)

    records = df.to_dict(orient="records")

    if not records:
        return 0

    inserted = 0

    with engine.begin() as connection:
        for start in range(0, len(records), 500):
            batch = records[start:start + 500]

            statement = insert(iot_measurements).values(batch)
            statement = statement.on_conflict_do_nothing(
                index_elements=["reading_id"]
            )

            result = connection.execute(statement)
            inserted += result.rowcount

    return inserted
