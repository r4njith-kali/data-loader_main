
"""End-to-end ThingWorx historical data ingestion."""

import logging

from src.demo.thingworx_adapter import (
    combine_property_histories,
)
from src.demo.measurement_loader import load_measurements

logger = logging.getLogger(__name__)


def ingest_thingworx_history(
    client,
    engine,
    device_id: str,
    property_names: list[str],
    start_date: str,
    end_date: str,
    max_items: int = 500,
) -> dict:
    """Fetch, normalize, and load historical sensor measurements."""
    responses = {}

    for property_name in property_names:
        endpoint = (
            f"Things/{device_id}/Services/"
            "QueryNumberPropertyHistory/"
        )

        parameters = {
            "propertyName": property_name,
            "startDate": start_date,
            "endDate": end_date,
            "maxItems": max_items,
            "oldestFirst": True,
        }

        responses[property_name] = client.post_request(
            endpoint,
            parameters=parameters,
        )

    measurements = combine_property_histories(
        device_id=device_id,
        responses=responses,
    )

    inserted = load_measurements(measurements, engine)

    summary = {
        "device_id": device_id,
        "properties": len(property_names),
        "extracted": len(measurements),
        "inserted": inserted,
    }

    logger.info("ThingWorx ingestion completed: %s", summary)

    return summary
