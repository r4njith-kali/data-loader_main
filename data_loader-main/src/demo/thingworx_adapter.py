
"""Convert ThingWorx property histories into ETL-ready records."""

import hashlib
from typing import Any, Dict, Iterable

import pandas as pd


def normalize_property_history(
    device_id: str,
    property_name: str,
    response: Dict[str, Any],
) -> pd.DataFrame:
    """Normalize a ThingWorx numeric property history response.

    Expected format:
        {"rows": [{"timestamp": 1767225600000, "value": 45.2}]}

    Timestamps are interpreted as Unix milliseconds in UTC.
    """
    if not isinstance(response, dict):
        raise ValueError("ThingWorx response must be a dictionary")

    rows = response.get("rows")

    if not isinstance(rows, list):
        raise ValueError("ThingWorx response must contain a rows list")

    records = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        timestamp = pd.to_datetime(
            row.get("timestamp"),
            unit="ms",
            utc=True,
            errors="coerce",
        )

        value = pd.to_numeric(
            row.get("value"),
            errors="coerce",
        )

        if pd.isna(timestamp) or pd.isna(value):
            continue

        identity = (
            f"{device_id}|{property_name}|"
            f"{timestamp.isoformat()}"
        )

        reading_id = hashlib.sha256(
            identity.encode("utf-8")
        ).hexdigest()

        records.append(
            {
                "reading_id": reading_id,
                "device_id": device_id,
                "property_name": property_name,
                "timestamp": timestamp,
                "value": float(value),
            }
        )

    return pd.DataFrame(
        records,
        columns=[
            "reading_id",
            "device_id",
            "property_name",
            "timestamp",
            "value",
        ],
    )


def combine_property_histories(
    device_id: str,
    responses: Dict[str, Dict[str, Any]],
) -> pd.DataFrame:
    """Combine multiple properties into a long-format dataset."""
    frames = [
        normalize_property_history(
            device_id=device_id,
            property_name=property_name,
            response=response,
        )
        for property_name, response in responses.items()
    ]

    if not frames:
        return pd.DataFrame(
            columns=[
                "reading_id",
                "device_id",
                "property_name",
                "timestamp",
                "value",
            ]
        )

    combined = pd.concat(frames, ignore_index=True)

    return (
        combined.drop_duplicates(subset=["reading_id"])
        .sort_values(["timestamp", "property_name"])
        .reset_index(drop=True)
    )
