
"""Tests for the Industrial IoT ETL pipeline."""

import pandas as pd
import pytest

from src.demo.pipeline import extract, transform


def test_extract_generates_expected_records():
    df = extract()

    assert len(df) == 120
    assert df["device_id"].nunique() == 5
    assert df["reading_id"].is_unique


def test_transform_preserves_valid_records():
    raw = extract()
    result = transform(raw)

    assert len(result) == 120
    assert result["reading_id"].is_unique
    assert result["quality_status"].eq("NORMAL").all()


def test_transform_removes_duplicates():
    raw = extract()
    duplicated = pd.concat(
        [raw, raw.iloc[[0]]],
        ignore_index=True,
    )

    result = transform(duplicated)

    assert len(result) == 120


def test_transform_rejects_invalid_measurements():
    raw = extract()

    raw.loc[0, "temperature_c"] = 999
    raw.loc[1, "vibration_mm_s"] = -5
    raw.loc[2, "power_kw"] = -10

    result = transform(raw)

    assert len(result) == 117


def test_transform_rejects_missing_columns():
    raw = extract().drop(columns=["device_id"])

    with pytest.raises(ValueError, match="Missing required columns"):
        transform(raw)


def test_transform_flags_abnormal_readings():
    raw = extract()

    raw.loc[0, "temperature_c"] = 95
    raw.loc[1, "vibration_mm_s"] = 5.5

    result = transform(raw)

    assert (
        result["quality_status"].eq("WARNING").sum() == 2
    )
