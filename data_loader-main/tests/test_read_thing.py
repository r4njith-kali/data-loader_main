
"""Tests for ThingWorx device discovery."""

from unittest.mock import Mock

import pytest

from src.utils.read_thing import GetThings


@pytest.fixture
def things():
    """Create an isolated GetThings instance without API access."""
    instance = GetThings.__new__(GetThings)

    instance.templateFromConfig = True
    instance.templateName = ["MOTOR_TEMPLATE", "INVERTER_TEMPLATE"]
    instance.client = Mock()

    return instance


def test_discovery_across_multiple_templates(things):
    things.client.get_request.side_effect = [
        {"rows": [{"name": "MOTOR-001"}, {"name": "MOTOR-002"}]},
        {"rows": [{"name": "INVERTER-001"}]},
    ]

    result = things.thing_name()

    assert result == [
        "MOTOR-001",
        "MOTOR-002",
        "INVERTER-001",
    ]
    assert things.client.get_request.call_count == 2


def test_discovery_removes_duplicates(things):
    things.client.get_request.side_effect = [
        {"rows": [{"name": "DEVICE-001"}]},
        {"rows": [{"name": "DEVICE-001"}, {"name": "DEVICE-002"}]},
    ]

    result = things.thing_name()

    assert result == ["DEVICE-001", "DEVICE-002"]


def test_discovery_rejects_invalid_response(things):
    things.client.get_request.return_value = {"unexpected": []}

    with pytest.raises(ValueError, match="rows"):
        things.thing_name()


def test_discovery_with_explicit_template(things):
    things.templateFromConfig = False
    things.client.get_request.return_value = {
        "rows": [{"name": "CUSTOM-001"}]
    }

    result = things.thing_name("CUSTOM_TEMPLATE")

    assert result == ["CUSTOM-001"]
    things.client.get_request.assert_called_once_with(
        "ThingTemplates/CUSTOM_TEMPLATE/ImplementingThings"
    )


def test_discovery_requires_explicit_template(things):
    things.templateFromConfig = False

    with pytest.raises(ValueError, match="template name"):
        things.thing_name()
