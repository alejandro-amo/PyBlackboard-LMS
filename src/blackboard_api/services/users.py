"""Convenience operations related to users."""

from __future__ import annotations

from typing import Any


class UserService:
    """Provide higher-level user operations."""

    def __init__(self, users_resource: Any) -> None:
        self.users = users_resource

    def change_username(
        self, *, current_username: str, new_username: str
    ) -> dict:
        """Change a username using the ``userName:...`` identifier."""
        if not isinstance(current_username, str) or not current_username.strip():
            raise ValueError("current_username must be a non-empty string")
        if not isinstance(new_username, str) or not new_username.strip():
            raise ValueError("new_username must be a non-empty string")
        if current_username == new_username:
            raise ValueError("new_username must differ from current_username")

        return self.users.update(
            user_identifier=f"userName:{current_username}",
            data={"userName": new_username},
        )
