
"""Tests for ThingWorx historical measurement normalization."""

import pytest

from src.demo.thingworx_adapter import (
    normalize_property_history,
    combine_property_histories,
)


def test_normalizes_history():
    response = {
        "rows": [
            {
                "timestamp": 1767225600000,
                "value": 45.2,
            }
        ]
    }

    result = normalize_property_history(
        "MOTOR-001", "MOTOR_TEMP", response
    )

    assert len(result) == 1
    assert result.iloc[0]["value"] == 45.2
    assert result.iloc[0]["property_name"] == "MOTOR_TEMP"
    assert str(result.iloc[0]["timestamp"].tzinfo) == "UTC"


def test_rejects_invalid_response():
    with pytest.raises(ValueError, match="rows list"):
        normalize_property_history(
            "MOTOR-001", "CURRENT", {"invalid": []}
        )


def test_skips_invalid_measurements():
    response = {
        "rows": [
            {"timestamp": 1767225600000, "value": 45.2},
            {"timestamp": None, "value": 50},
            {"timestamp": 1767225601000, "value": "invalid"},
        ]
    }

    result = normalize_property_history(
        "MOTOR-001", "MOTOR_TEMP", response
    )

    assert len(result) == 1


def test_combines_multiple_properties():
    responses = {
        "MOTOR_TEMP": {
            "rows": [
                {"timestamp": 1767225600000, "value": 45.2}
            ]
        },
        "CURRENT": {
            "rows": [
                {"timestamp": 1767225601000, "value": 12.5}
            ]
        },
    }

    result = combine_property_histories(
        "MOTOR-001", responses
    )

    assert len(result) == 2
    assert set(result["property_name"]) == {
        "MOTOR_TEMP",
        "CURRENT",
    }


def test_generates_stable_reading_ids():
    response = {
        "rows": [
            {"timestamp": 1767225600000, "value": 45.2}
        ]
    }

    first = normalize_property_history(
        "MOTOR-001", "MOTOR_TEMP", response
    )

    second = normalize_property_history(
        "MOTOR-001", "MOTOR_TEMP", response
    )

    assert first.iloc[0]["reading_id"] == (
        second.iloc[0]["reading_id"]
    )
