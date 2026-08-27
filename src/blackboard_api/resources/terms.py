"""Atomic operations for Blackboard academic terms."""

from __future__ import annotations

import logging
from typing import Any, Iterator

from ..identifiers import (
    TERM_IDENTIFIER_POLICY,
    encode_identifier,
    validate_creation_data,
    validate_data,
    validate_identifier,
)

logger = logging.getLogger(__name__)


class TermResource:
    """CRUD operations for terms through the public v1 endpoints."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def list(self) -> list[dict]:
        """List all terms while resolving pagination."""
        return list(self.iter())

    def iter(self) -> Iterator[dict]:
        """Iterate over all terms without accumulating the full collection."""
        return self.client._iter_paginated("/learn/api/public/v1/terms")

    def get(self, *, term_identifier: str) -> dict:
        """Get a term by primary ID or ``externalId``."""
        identifier = validate_identifier(
            term_identifier,
            name="term_identifier",
            policy=TERM_IDENTIFIER_POLICY,
        )
        path = f"/learn/api/public/v1/terms/{encode_identifier(identifier)}"
        return self.client._request_json("GET", path)

    def create(self, data: dict) -> dict:
        """Create a term; Blackboard generates its primary ID."""
        return self.client._request_json(
            "POST",
            "/learn/api/public/v1/terms",
            json=validate_creation_data(data),
        )

    def update(self, *, term_identifier: str, data: dict) -> dict:
        """Update a term by primary ID or ``externalId``."""
        identifier = validate_identifier(
            term_identifier,
            name="term_identifier",
            policy=TERM_IDENTIFIER_POLICY,
        )
        path = f"/learn/api/public/v1/terms/{encode_identifier(identifier)}"
        return self.client._request_json(
            "PATCH", path, json=validate_data(data)
        )

    def delete(self, *, term_identifier: str) -> None:
        """Delete a term by primary ID or ``externalId``."""
        identifier = validate_identifier(
            term_identifier,
            name="term_identifier",
            policy=TERM_IDENTIFIER_POLICY,
        )
        path = f"/learn/api/public/v1/terms/{encode_identifier(identifier)}"
        self.client._request("DELETE", path)
