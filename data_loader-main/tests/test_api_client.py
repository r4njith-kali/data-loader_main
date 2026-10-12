
"""Unit tests for the ThingWorx HTTP client."""

from unittest.mock import Mock

import pytest
import requests

from src.utils.api_client import ApiClient


@pytest.fixture
def client(tmp_path):
    config = tmp_path / "api.yaml"
    config.write_text(
        "host_url: https://example.test/Thingworx/\n"
        "api_key: test-key\n",
        encoding="utf-8",
    )

    session = Mock(spec=requests.Session)

    client = ApiClient(
        config_file=str(config),
        session=session,
        timeout=5,
    )

    return client


def test_get_request(client):
    response = Mock()
    response.content = b'{"rows": []}'
    response.json.return_value = {"rows": []}
    client.session.request.return_value = response

    result = client.get_request("Things")

    assert result == {"rows": []}

    client.session.request.assert_called_once()
    args, kwargs = client.session.request.call_args

    assert args == (
        "GET",
        "https://example.test/Thingworx/Things",
    )
    assert kwargs["timeout"] == 5
    assert kwargs["headers"]["appKey"] == "test-key"


def test_post_preserves_query_parameters(client):
    response = Mock()
    response.content = b'{"rows": []}'
    response.json.return_value = {"rows": []}
    client.session.request.return_value = response

    client.post_request(
        "Things/MOTOR-001/Services/Test",
        {"propertyName": "CURRENT"},
    )

    _, kwargs = client.session.request.call_args

    assert kwargs["params"] == {
        "propertyName": "CURRENT"
    }


def test_http_error_raises_exception(client):
    response = Mock()
    response.raise_for_status.side_effect = (
        requests.exceptions.HTTPError(
            "Server error",
            response=Mock(status_code=500),
        )
    )
    client.session.request.return_value = response

    with pytest.raises(RuntimeError, match="HTTP 500"):
        client.get_request("Things")


def test_timeout_raises_exception(client):
    client.session.request.side_effect = (
        requests.exceptions.Timeout()
    )

    with pytest.raises(RuntimeError, match="timed out"):
        client.get_request("Things")


def test_invalid_json_raises_exception(client):
    response = Mock()
    response.content = b"not-json"
    response.json.side_effect = ValueError("Invalid JSON")
    client.session.request.return_value = response

    with pytest.raises(ValueError, match="Invalid JSON"):
        client.get_request("Things")
