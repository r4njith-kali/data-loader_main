
"""HTTP client for ThingWorx REST API integrations."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import yaml

logger = logging.getLogger(__name__)


class ApiClient:
    """Configurable ThingWorx API client."""

    def __init__(
        self,
        config_file: str = "",
        debug: bool = False,
        timeout: int = 30,
        session: Optional[requests.Session] = None,
    ):
        self.url = ""
        self.api_key = ""
        self.proxies: Dict[str, str] = {}
        self.timeout = timeout
        self.session = session or requests.Session()

        if debug:
            logger.setLevel(logging.DEBUG)

        self.configure(config_file)

    def configure(self, config_file: str) -> None:
        """Load connection settings from YAML and environment."""
        if not config_file:
            raise ValueError("A configuration file is required")

        with Path(config_file).open(encoding="utf-8") as stream:
            config = yaml.safe_load(stream) or {}

        if not isinstance(config, dict):
            raise ValueError("API configuration must be a YAML mapping")

        self.url = str(
            os.getenv("THINGWORX_URL")
            or config.get("host_url")
            or ""
        ).rstrip("/") + "/"

        self.api_key = str(
            os.getenv("THINGWORX_API_KEY")
            or config.get("api_key")
            or ""
        )

        if not self.url.strip("/"):
            raise ValueError("ThingWorx host URL is missing")

        if not self.api_key:
            raise ValueError("ThingWorx API key is missing")

        proxy = config.get("proxy")
        self.proxies = {"https": proxy} if proxy else {}

        if config.get("debug"):
            logger.setLevel(logging.DEBUG)

    def _request(
        self,
        method: str,
        api: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute an HTTP request and decode its JSON response."""
        url = self.url + api.lstrip("/")

        headers = {
            "appKey": self.api_key,
            "Accept": "application/json",
        }

        kwargs: Dict[str, Any] = {
            "headers": headers,
            "timeout": self.timeout,
            "proxies": self.proxies,
        }

        if method == "GET":
            kwargs["params"] = parameters
        elif method == "POST":
            # Preserve the original client's query-parameter behavior.
            headers["Content-Type"] = "application/json"
            kwargs["params"] = parameters
        elif method == "PUT":
            # Preserve the original client's raw-body behavior.
            headers["Content-Type"] = "application/json"
            kwargs["data"] = parameters

        try:
            response = self.session.request(
                method, url, **kwargs
            )
            response.raise_for_status()

            if not response.content:
                return None

            return response.json()

        except requests.exceptions.Timeout as exc:
            logger.error("ThingWorx request timed out: %s", method)
            raise RuntimeError(
                "ThingWorx API request timed out"
            ) from exc

        except requests.exceptions.HTTPError as exc:
            status = (
                exc.response.status_code
                if exc.response is not None
                else "unknown"
            )
            logger.error(
                "ThingWorx HTTP error: %s", status
            )
            raise RuntimeError(
                f"ThingWorx API returned HTTP {status}"
            ) from exc

        except requests.exceptions.RequestException as exc:
            logger.error("ThingWorx network request failed")
            raise RuntimeError(
                "ThingWorx API request failed"
            ) from exc

        except ValueError as exc:
            logger.error("ThingWorx returned invalid JSON")
            raise ValueError(
                "Invalid JSON returned by ThingWorx API"
            ) from exc

    def get_request(
        self, api: str, parameters: Optional[dict] = None
    ) -> Any:
        return self._request("GET", api, parameters)

    def post_request(
        self, api: str, parameters: Optional[dict] = None
    ) -> Any:
        return self._request("POST", api, parameters)

    def put_request(
        self, api: str, parameters: Optional[dict] = None
    ) -> Any:
        return self._request("PUT", api, parameters)
