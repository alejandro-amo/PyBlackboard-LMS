"""Base fixture and identifier compatibility tests."""

from __future__ import annotations

import time
import unittest

from tests.integration.fixtures import get_test_resources


class WriteFixtureCreationTests(unittest.TestCase):
    """Create and retrieve the fixed resource graph used by later tests."""

    def test_10_create_base_fixtures(self) -> None:
        """Create two terms, two nodes, five users, and two courses."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        self.assertEqual(len(resources.terms), 2)
        self.assertEqual(len(resources.nodes), 2)
        self.assertEqual(len(resources.users), 5)
        self.assertEqual(len(resources.courses), 2)

    def test_20_fixtures_are_readable_by_supported_identifier_types(self) -> None:
        """Read every fixture through each identifier type it actually exposes."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        time.sleep(2)
        self.assert_resources_readable(resources.terms, resources.client.terms.get,
                                       "term_identifier", ("externalId",))
        self.assert_resources_readable(resources.nodes, resources.client.nodes.get,
                                       "node_identifier", ("externalId",))
        self.assert_resources_readable(
            resources.users,
            resources.client.users.get,
            "user_identifier",
            ("externalId", "userName", "uuid"),
        )
        self.assert_resources_readable(
            resources.courses,
            resources.client.courses.get,
            "course_identifier",
            ("externalId", "courseId", "uuid"),
        )

    def assert_resources_readable(
        self,
        resources: list[dict],
        get: object,
        identifier_name: str,
        explicit_types: tuple[str, ...],
    ) -> None:
        for resource in resources:
            identifiers = [resource["id"]]
            identifiers.extend(
                f"{identifier_type}:{resource[identifier_type]}"
                for identifier_type in explicit_types
                if resource.get(identifier_type)
            )
            for identifier in identifiers:
                with self.subTest(identifier=identifier):
                    found = get(**{identifier_name: identifier})
                    self.assertEqual(found["id"], resource["id"])


if __name__ == "__main__":
    unittest.main()
