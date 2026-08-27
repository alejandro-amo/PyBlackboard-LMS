from __future__ import annotations

from typing import Any
import logging

import requests

from .errors import AuthenticationError, TransportError

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self, base_url: str, client_id: str, client_secret: str, transport: Any
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._transport = transport
        self.token = None
        self.token_expires_at = 0

    def is_token_expired(self, now: float) -> bool:
        return self.token is None or now >= self.token_expires_at

    def request_access_token(self) -> dict[str, Any]:
        logger.debug("Requesting OAuth token from Blackboard")
        try:
            response = self._transport.request(
                "POST",
                f"{self.base_url}/learn/api/public/v1/oauth2/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"grant_type": "client_credentials"},
                auth=(self.client_id, self.client_secret),
                track_api_quota=False,
            )
        except TransportError as exc:
            logger.warning("Could not reach the authentication endpoint")
            raise AuthenticationError(
                "Could not reach the authentication endpoint"
            ) from exc
        try:
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError as exc:
            logger.warning("Blackboard rejected OAuth authentication")
            raise AuthenticationError(
                "Blackboard rejected authentication credentials"
            ) from exc
        except ValueError as exc:
            logger.warning("Blackboard returned invalid JSON during authentication")
            raise AuthenticationError("Authentication JSON response is invalid") from exc
        if not isinstance(data, dict) or not data.get("access_token"):
            logger.warning("OAuth response does not contain a valid access_token")
            raise AuthenticationError(
                "Authentication response does not contain access_token"
            )
        return data

    def authenticate(self, now: float) -> str:
        if not self.is_token_expired(now):
            logger.debug("Reusing valid OAuth token")
            return self.token
        data = self.request_access_token()
        self.token = data["access_token"]
        try:
            expires_in = max(1, int(data.get("expires_in", 3600)))
        except (TypeError, ValueError) as exc:
            raise AuthenticationError(
                "Authentication response contains invalid expires_in"
            ) from exc
        # Prevent very short-lived tokens from expiring immediately.
        skew = min(60, max(0, expires_in // 10))
        self.token_expires_at = now + expires_in - skew
        logger.debug("OAuth token obtained; expiry uses a safety margin")
        return self.token
