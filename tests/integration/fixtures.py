"""Shared temporary resources for write-enabled integration tests."""

from __future__ import annotations

import atexit
import logging
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from blackboard_api import BlackboardAPI
from blackboard_api.config import api_config_from_environment


logger = logging.getLogger(__name__)
TEST_ENV_FILE = Path(__file__).resolve().parents[2] / ".env.test.local"
_resources: TestResources | None = None


@dataclass
class TestResources:
    """Resources created for a single integration-test run."""

    client: BlackboardAPI
    prefix: str = field(default_factory=lambda: f"BBCLI-IT-{uuid4().hex[:12]}")
    terms: list[dict] = field(default_factory=list)
    nodes: list[dict] = field(default_factory=list)
    users: list[dict] = field(default_factory=list)
    courses: list[dict] = field(default_factory=list)
    enrollments: dict[tuple[str, str], dict] = field(default_factory=dict)

    def create_base_fixtures(self) -> None:
        """Create two terms, nodes, and courses, plus five users."""
        if self.terms:
            logger.debug("Reusing integration-test resources: %s", self.prefix)
            return
        logger.info("Creating integration-test resources: %s", self.prefix)
        try:
            self.terms = [self._create_term(index) for index in range(1, 3)]
            self.nodes = [self._create_node(index) for index in range(1, 3)]
            self.users = [self._create_user(index) for index in range(1, 6)]
            self.courses = [self._create_course(index) for index in range(1, 3)]
        except Exception:
            self.cleanup()
            raise

    def create_enrollment(self, *, user: dict, course: dict) -> dict:
        """Create and record one enrollment when it does not already exist."""
        key = (course["id"], user["id"])
        if key not in self.enrollments:
            self.enrollments[key] = self.client.enrollments.create(
                course_identifier=course["id"],
                user_identifier=user["id"],
                course_role_id="Student",
            )
        return self.enrollments[key]

    def delete_enrollment(self, *, user: dict, course: dict) -> None:
        """Delete a recorded enrollment and remove it from the fixture state."""
        key = (course["id"], user["id"])
        self.client.enrollments.delete(
            course_identifier=course["id"],
            user_identifier=user["id"],
        )
        self.enrollments.pop(key, None)

    def identifiers(self) -> dict[str, list[str]]:
        """Return primary identifiers required to verify final cleanup."""
        self.create_base_fixtures()
        return {
            "terms": [term["id"] for term in self.terms],
            "nodes": [node["id"] for node in self.nodes],
            "users": [user["id"] for user in self.users],
            "courses": [course["id"] for course in self.courses],
        }

    def cleanup(self, *, strict: bool = False) -> None:
        """Delete all test resources in reverse dependency order."""
        for course_id, user_id in list(self.enrollments):
            self._run_cleanup(
                f"enrollment {course_id}/{user_id}",
                lambda course_id=course_id, user_id=user_id: (
                    self.client.enrollments.delete(
                        course_identifier=course_id,
                        user_identifier=user_id,
                    )
                ),
                strict,
            )
            self.enrollments.pop((course_id, user_id), None)

        for user in reversed(self.users):
            for node in reversed(self.nodes):
                self._run_cleanup(
                    f"user-node association {user['id']}/{node['id']}",
                    lambda user=user, node=node: self.client.users.unassign_node(
                        user_identifier=user["id"],
                        node_identifier=node["id"],
                    ),
                    strict,
                    ignore_not_found=True,
                )
        self._delete_collection(
            "course", self.courses, self.client.courses.delete,
            "course_identifier", strict,
        )
        self._delete_collection(
            "user", self.users, self.client.users.delete,
            "user_identifier", strict,
        )
        self._delete_collection(
            "node", self.nodes, self.client.nodes.delete,
            "node_identifier", strict,
        )
        self._delete_collection(
            "term", self.terms, self.client.terms.delete,
            "term_identifier", strict,
        )

    def _create_term(self, index: int) -> dict:
        term = self.client.terms.create(
            {
                "externalId": f"{self.prefix}-TERM-{index}",
                "name": f"{self.prefix} term {index}",
            }
        )
        return self._require_primary_id(term, f"term {index}")

    def _create_node(self, index: int) -> dict:
        node = self.client.nodes.create(
            {
                "externalId": f"{self.prefix}-NODE-{index}",
                "title": f"{self.prefix} node {index}",
            }
        )
        return self._require_primary_id(node, f"node {index}")

    def _create_user(self, index: int) -> dict:
        user = self.client.users.create(
            {
                "externalId": f"{self.prefix}-USER-{index}",
                "userName": f"{self.prefix.lower()}-user-{index}@test.invalid",
                "password": f"BbCliIt!{secrets.token_urlsafe(18)}",
                "name": {
                    "given": "Blackboard",
                    "family": f"Integration {self.prefix} {index}",
                },
            }
        )
        return self._require_primary_id(user, f"user {index}")

    def _create_course(self, index: int) -> dict:
        course = self.client.courses.create(
            {
                "courseId": f"{self.prefix}-COURSE-{index}",
                "externalId": f"{self.prefix}-COURSE-EXTERNAL-{index}",
                "name": f"{self.prefix} course {index}",
            }
        )
        return self._require_primary_id(course, f"course {index}")

    def _delete_collection(
        self,
        name: str,
        resources: list[dict],
        delete: object,
        identifier_name: str,
        strict: bool,
    ) -> None:
        for resource in reversed(resources):
            self._run_cleanup(
                f"{name} {resource['id']}",
                lambda resource=resource: delete(
                    **{identifier_name: resource["id"]}
                ),
                strict,
            )
        resources.clear()

    def _run_cleanup(
        self,
        name: str,
        operation: object,
        strict: bool,
        *,
        ignore_not_found: bool = False,
    ) -> None:
        try:
            operation()
        except Exception as exc:
            if ignore_not_found and exc.__class__.__name__ == "NotFoundError":
                return
            if strict:
                raise
            logger.exception("Could not clean up test %s", name)
        else:
            logger.info("Deleted test %s for %s", name, self.prefix)

    @staticmethod
    def _require_primary_id(resource: dict, resource_name: str) -> dict:
        if not isinstance(resource, dict) or not resource.get("id"):
            raise AssertionError(
                f"Created {resource_name} does not contain a primary ID"
            )
        return resource


def get_test_resources() -> TestResources:
    """Return the shared writable resources for this integration-test process."""
    global _resources
    if _resources is None:
        try:
            api_config_from_environment(TEST_ENV_FILE)
        except (FileNotFoundError, ValueError) as exc:
            raise RuntimeError(
                "Write integration tests require a valid .env.test.local file"
            ) from exc
        _resources = TestResources(
            BlackboardAPI(env_file=str(TEST_ENV_FILE), enable_write=True)
        )
    return _resources


@atexit.register
def _emergency_cleanup() -> None:
    """Avoid leaked test data if only part of the integration suite is run."""
    if _resources is not None:
        _resources.cleanup()
