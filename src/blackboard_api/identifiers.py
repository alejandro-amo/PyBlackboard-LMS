"""Validation helpers for Blackboard identifiers and request bodies."""

from dataclasses import dataclass
from urllib.parse import quote
from .errors import BlackboardAPIError


SYSTEM_GENERATED_CREATE_FIELDS = frozenset({"id", "uuid"})


class InvalidIdentifierError(BlackboardAPIError, ValueError):
    """Raised when an identifier uses an unsupported explicit type."""


@dataclass(frozen=True)
class IdentifierPolicy:
    """Describe the explicit identifier types accepted by a resource."""

    explicit_types: frozenset[str]
    primary_allowed: bool = True


def validate_identifier(
    value: str, *, name: str, policy: IdentifierPolicy
) -> str:
    """Validate a primary or explicitly typed Blackboard identifier."""
    if not isinstance(value, str) or not value.strip():
        raise InvalidIdentifierError(f"{name} must be a non-empty string")

    if ":" not in value:
        if not policy.primary_allowed:
            raise InvalidIdentifierError(f"{name} must include an explicit type")
        return value

    identifier_type, identifier_value = value.split(":", 1)
    if identifier_type not in policy.explicit_types or not identifier_value:
        allowed = ", ".join(sorted(policy.explicit_types))
        raise InvalidIdentifierError(
            f"{name} uses an invalid type; allowed types: {allowed}"
        )
    return value


def encode_identifier(value: str) -> str:
    """Encode an already validated identifier for use as one URL path segment."""
    return quote(value, safe=":")


def validate_data(data: dict, *, name: str = "data") -> dict:
    """Validate that a request body is a dictionary."""
    if not isinstance(data, dict):
        raise ValueError(f"{name} must be a dictionary")
    return data


def validate_creation_data(data: dict, *, name: str = "data") -> dict:
    """Reject system-generated identifiers in a resource creation body."""
    data = validate_data(data, name=name)
    forbidden = sorted(SYSTEM_GENERATED_CREATE_FIELDS.intersection(data))
    if forbidden:
        fields = ", ".join(forbidden)
        raise ValueError(
            f"{name} must not include system-generated field(s): {fields}"
        )
    return data


def validate_primary(primary: bool | None) -> bool | None:
    if primary is not None and not isinstance(primary, bool):
        raise TypeError("primary must be a bool or None")
    return primary


COURSE_IDENTIFIER_POLICY = IdentifierPolicy(
    frozenset({"externalId", "courseId", "uuid"})
)
USER_IDENTIFIER_POLICY = IdentifierPolicy(
    frozenset({"externalId", "userName", "uuid"})
)
NODE_IDENTIFIER_POLICY = IdentifierPolicy(frozenset({"externalId"}))
TERM_IDENTIFIER_POLICY = IdentifierPolicy(frozenset({"externalId"}))
