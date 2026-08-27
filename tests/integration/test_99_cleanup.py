"""Final verified cleanup for the shared integration-test resource graph."""

from __future__ import annotations

import time
import unittest

from blackboard_api.errors import NotFoundError
from tests.integration.fixtures import get_test_resources


class CleanupTests(unittest.TestCase):
    """Must remain the final integration-test module by filename convention."""

    def test_99_resources_are_deleted_and_no_longer_readable(self) -> None:
        """Delete every fixture and verify all primary IDs return NotFoundError."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        identifiers = resources.identifiers()
        resources.cleanup(strict=True)
        time.sleep(2)

        self.assert_resources_absent(
            identifiers["terms"], resources.client.terms.get, "term_identifier"
        )
        self.assert_resources_absent(
            identifiers["nodes"], resources.client.nodes.get, "node_identifier"
        )
        self.assert_resources_absent(
            identifiers["users"], resources.client.users.get, "user_identifier"
        )
        self.assert_resources_absent(
            identifiers["courses"], resources.client.courses.get,
            "course_identifier",
        )

    def assert_resources_absent(
        self, identifiers: list[str], get: object, identifier_name: str
    ) -> None:
        """Assert that all supplied primary identifiers are no longer readable."""
        for identifier in identifiers:
            with self.subTest(identifier=identifier):
                with self.assertRaises(NotFoundError):
                    get(**{identifier_name: identifier})


if __name__ == "__main__":
    unittest.main()
