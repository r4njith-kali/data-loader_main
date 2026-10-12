
"""Integration tests for the original SDM telemetry ingestion path."""

import os
from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pandas as pd
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    MetaData,
    String,
    Table,
    create_engine,
    inspect,
    select,
    func,
)

from src.sdm.sdm_pipeline import SDM_PIPELINE


def test_sdm_pipeline_uses_incremental_bulk_loading(monkeypatch):
    url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg2://etl_user:local_demo_only@127.0.0.1:5433/industrial_iot",
    )

    engine = create_engine(url)
    metadata = MetaData()
    table_name = f"test_sdm_{uuid4().hex[:12]}"

    table = Table(
        table_name,
        metadata,
        Column("id", String, primary_key=True),
        Column("timestamp", DateTime(timezone=True)),
        Column("thingworx_name", String),
        Column("cell", String),
        Column("current", Float),
        Column("gap_value", Float),
        Column("pow_unit_temp", Float),
        Column("cu_temp", Float),
        Column("output_v", Float),
        Column("speed", Float),
        Column("torque", Float),
        Column("updated_timestamp", DateTime(timezone=True)),
        schema="public",
    )

    metadata.create_all(engine)

    try:
        pipeline = SDM_PIPELINE.__new__(SDM_PIPELINE)

        pipeline.eng = engine
        pipeline.insp = inspect(engine)
        pipeline.schema = "public"
        pipeline.now = datetime.now(timezone.utc)
        pipeline.twx_config = "unused-test-config"
        pipeline.start_str = "20260101"
        pipeline.end_str = "20260102"

        pipeline.sdm = Mock()
        pipeline.sdm.get_thing_info.return_value = pd.DataFrame(
            [{"cell": "CELL-A", "facility_no": "FAC-001"}]
        )

        pipeline.get_things = Mock()
        pipeline.get_things.get_prod_date.return_value = [
            "20260101"
        ]

        pipeline.gen_date = Mock()

        readings = pd.DataFrame([
            {
                "id": "1767225600_FAC-001",
                "timestamp": datetime(
                    2026, 1, 1, tzinfo=timezone.utc
                ),
                "thingworx_name": "MOTOR-001",
                "cell": "CELL-A",
                "CURRENT": 12.5,
                "GAPVALUE": 0.2,
                "POW_UNIT_TEMP": 42.0,
                "CU_TEMP": 39.0,
                "OUTPUT_V": 220.0,
                "SPEED": 1450.0,
                "TORQUE": 18.5,
            },
            {
                "id": "1767225660_FAC-001",
                "timestamp": datetime(
                    2026, 1, 1, 0, 1, tzinfo=timezone.utc
                ),
                "thingworx_name": "MOTOR-001",
                "cell": "CELL-A",
                "CURRENT": 12.7,
                "GAPVALUE": 0.3,
                "POW_UNIT_TEMP": 42.2,
                "CU_TEMP": 39.1,
                "OUTPUT_V": 220.0,
                "SPEED": 1451.0,
                "TORQUE": 18.7,
            },
        ])

        pipeline.get_thing_vs = Mock(
            return_value=readings.copy()
        )

        def fake_config_param(config_file, field):
            if field == "SEW_INVERTER_TEMPLATE":
                return (
                    "CURRENT,GAPVALUE,POW_UNIT_TEMP,"
                    "CU_TEMP,OUTPUT_V,SPEED,TORQUE"
                )
            raise ValueError(f"Unexpected config field: {field}")

        monkeypatch.setattr(
            "src.sdm.sdm_pipeline.config_param",
            fake_config_param,
        )

        # Mock only the equipment lookup query.
        original_read_sql = pd.read_sql_query

        def mock_read_sql(query, con, **kwargs):
            if "mtr_tbl_info" in str(query):
                return pd.DataFrame(
                    [{"thingworx_name": "MOTOR-001"}]
                )
            return original_read_sql(query, con, **kwargs)

        monkeypatch.setattr(
            "src.sdm.sdm_pipeline.pd.read_sql_query",
            mock_read_sql,
        )

        for _ in range(2):
            pipeline.load_mtr_vs(
                template="SEW_INVERTER_TEMPLATE",
                raw_tbl=table_name,
                prodOnly=True,
            )

        with engine.connect() as connection:
            count = connection.scalar(
                select(func.count()).select_from(table)
            )

        assert count == 2
        assert pipeline.get_thing_vs.call_count == 2
        assert inspect(engine).get_pk_constraint(
            table_name, schema="public"
        )["constrained_columns"] == ["id"]

    finally:
        metadata.drop_all(engine)
        engine.dispose()
