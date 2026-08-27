"""Ordered, reversible mutations of the shared integration-test fixtures."""

from __future__ import annotations

import csv
import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest

from blackboard_cli.cli import _write_result
from tests.integration.fixtures import get_test_resources


class MutationTests(unittest.TestCase):
    """Validate updates, availability, enrollments, and node associations."""

    def test_10_comprehensive_updates_are_persisted(self) -> None:
        """Update one term, node, user, and course, then verify every change."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        term = resources.terms[0]
        node = resources.nodes[0]
        user = resources.users[0]
        course = resources.courses[0]
        suffix = " updated"
        updated_username = f"{resources.prefix.lower()}-updated@test.invalid"

        resources.client.terms.update(
            term_identifier=term["id"],
            data={
                "externalId": f"{resources.prefix}-TERM-UPDATED",
                "name": f"{resources.prefix}{suffix}",
            },
        )
        resources.client.nodes.update(
            node_identifier=node["id"],
            data={
                "externalId": f"{resources.prefix}-NODE-UPDATED",
                "title": f"{resources.prefix}{suffix}",
                "description": "Updated integration node",
            },
        )
        resources.client.users.update(
            user_identifier=user["id"],
            data={
                "externalId": f"{resources.prefix}-USER-UPDATED",
                "name": {"given": "Updated", "family": "Integration"},
                "contact": {"email": "updated@test.invalid"},
            },
        )
        resources.client.users.change_username(
            current_username=user["userName"],
            new_username=updated_username,
        )
        resources.client.courses.update(
            course_identifier=course["id"],
            data={
                "externalId": f"{resources.prefix}-COURSE-UPDATED",
                "name": f"{resources.prefix}{suffix}",
                "description": "Updated integration course",
            },
        )

        self.wait_for_consistency()
        updated_term = resources.client.terms.get(term_identifier=term["id"])
        self.assertEqual(updated_term["name"], f"{resources.prefix}{suffix}")
        self.assertEqual(
            updated_term["externalId"], f"{resources.prefix}-TERM-UPDATED"
        )
        updated_node = resources.client.nodes.get(node_identifier=node["id"])
        self.assertEqual(updated_node["description"], "Updated integration node")
        self.assertEqual(
            updated_node["externalId"], f"{resources.prefix}-NODE-UPDATED"
        )
        updated_user = resources.client.users.get(
            user_identifier=f"userName:{updated_username}"
        )
        self.assertEqual(updated_user["id"], user["id"])
        self.assertEqual(updated_user["name"]["given"], "Updated")
        self.assertEqual(updated_user["externalId"], f"{resources.prefix}-USER-UPDATED")
        updated_course = resources.client.courses.get(course_identifier=course["id"])
        self.assertEqual(updated_course["description"], "Updated integration course")
        self.assertEqual(
            updated_course["externalId"], f"{resources.prefix}-COURSE-UPDATED"
        )

    def test_20_availability_transitions_are_persisted(self) -> None:
        """Transition one user and one course through all supported states."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        cases = (
            (resources.client.users, "user_identifier", resources.users[0]["id"]),
            (
                resources.client.courses,
                "course_identifier",
                resources.courses[0]["id"],
            ),
        )
        for facade, identifier_name, identifier in cases:
            for method_name, expected in (
                ("set_unavailable", "No"),
                ("set_disabled", "Disabled"),
                ("set_available", "Yes"),
            ):
                with self.subTest(method=method_name, identifier=identifier):
                    getattr(facade, method_name)(**{identifier_name: identifier})
                    self.wait_for_consistency()
                    current = facade.get(**{identifier_name: identifier})
                    self.assertEqual(current["availability"]["available"], expected)

    def test_30_create_course_one_enrollments_and_list_course(self) -> None:
        """Enroll every user in course one and verify the bounded course list."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        course = resources.courses[0]
        for user in resources.users:
            resources.create_enrollment(user=user, course=course)
        self.wait_for_consistency()
        self.assert_course_has_users(course, resources.users)

    def test_40_create_course_two_enrollments_and_list_course(self) -> None:
        """Enroll every user in course two and verify the bounded course list."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        course = resources.courses[1]
        for user in resources.users:
            resources.create_enrollment(user=user, course=course)
        self.wait_for_consistency()
        self.assert_course_has_users(course, resources.users)

    def test_50_each_user_has_two_enrollments(self) -> None:
        """Verify each fixture user has the two expected course enrollments."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        self.wait_for_consistency()
        expected_course_ids = {course["id"] for course in resources.courses}
        for user in resources.users:
            with self.subTest(user_id=user["id"]):
                enrollments = resources.client.enrollments.list_by_user(
                    user_identifier=user["id"]
                )
                course_ids = {
                    item.get("courseId") or item.get("id")
                    for item in enrollments
                }
                self.assertTrue(expected_course_ids.issubset(course_ids))

    def test_55_export_fixture_resources_to_files_and_standard_output(self) -> None:
        """Export live fixture data through every supported safe destination."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        self.wait_for_consistency()
        cases = {
            "terms": resources.terms,
            "nodes": resources.nodes,
            "users": resources.users,
            "courses": resources.courses,
            "enrollments": resources.client.enrollments.list_by_course(
                course_identifier=resources.courses[0]["id"]
            ),
            "enrollment_roles": resources.client.enrollment_roles.list(),
        }
        for resource_name, result in cases.items():
            with self.subTest(resource=resource_name):
                self.assertIsInstance(result, list)
                self.assertTrue(result)
                self.assert_file_exports(resource_name, result)
                self.assert_standard_output_exports(result)

    def assert_file_exports(self, resource_name: str, result: list[dict]) -> None:
        """Write and validate CSV, Excel, and JSON files for one resource."""
        with TemporaryDirectory() as directory:
            output_directory = Path(directory)
            csv_path = output_directory / f"{resource_name}.csv"
            excel_path = output_directory / f"{resource_name}.xlsx"
            json_path = output_directory / f"{resource_name}.json"
            _write_result(result, "csv", str(csv_path))
            _write_result(result, "excel", str(excel_path))
            _write_result(result, "json", str(json_path))

            with csv_path.open(encoding="utf-8", newline="") as stream:
                self.assertTrue(list(csv.DictReader(stream)))
            self.assertGreater(excel_path.stat().st_size, 0)
            with excel_path.open("rb") as stream:
                self.assertEqual(stream.read(2), b"PK")
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), result)

    def assert_standard_output_exports(self, result: list[dict]) -> None:
        """Validate CSV and JSON text output plus Excel's safe rejection."""
        for output_format in ("csv", "json"):
            with self.subTest(format=output_format):
                stream = StringIO()
                with redirect_stdout(stream):
                    _write_result(result, output_format, None)
                text = stream.getvalue()
                self.assertTrue(text)
                if output_format == "csv":
                    self.assertTrue(list(csv.DictReader(StringIO(text))))
                else:
                    self.assertEqual(json.loads(text), result)
        with self.assertRaisesRegex(ValueError, "--output is required"):
            _write_result(result, "excel", None)

    def test_60_delete_enrollments_and_verify_course_lists(self) -> None:
        """Remove all test enrollments and verify both bounded course lists."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        for course in resources.courses:
            for user in resources.users:
                resources.delete_enrollment(user=user, course=course)
        self.wait_for_consistency()
        for course in resources.courses:
            with self.subTest(course_id=course["id"]):
                enrollments = resources.client.enrollments.list_by_course(
                    course_identifier=course["id"]
                )
                enrolled_ids = {
                    self.enrollment_user_id(item) for item in enrollments
                }
                self.assertFalse(
                    {user["id"] for user in resources.users} & enrolled_ids
                )

    def test_70_assign_all_users_to_primary_node(self) -> None:
        """Assign every user to node one as primary and verify its user list."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        node = resources.nodes[0]
        for user in resources.users:
            resources.client.users.assign_node(
                user_identifier=user["id"],
                node_identifier=node["id"],
                primary=True,
            )
        self.wait_for_consistency()
        self.assert_node_has_users(node, resources.users)

    def test_80_assign_all_users_to_secondary_node(self) -> None:
        """Assign every user to node two as non-primary and verify its user list."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        node = resources.nodes[1]
        for user in resources.users:
            resources.client.users.assign_node(
                user_identifier=user["id"],
                node_identifier=node["id"],
                primary=False,
            )
        self.wait_for_consistency()
        self.assert_node_has_users(node, resources.users)

    def test_90_unassign_all_users_from_nodes(self) -> None:
        """Remove every test user from both nodes and verify both user lists."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        for node in resources.nodes:
            for user in resources.users:
                resources.client.users.unassign_node(
                    user_identifier=user["id"],
                    node_identifier=node["id"],
                )
        self.wait_for_consistency()
        expected_user_ids = {user["id"] for user in resources.users}
        for node in resources.nodes:
            with self.subTest(node_id=node["id"]):
                users = resources.client.users.list_by_node(
                    node_identifier=node["id"]
                )
                node_user_ids = {self.user_id(item) for item in users}
                self.assertFalse(expected_user_ids & node_user_ids)

    def test_91_assign_courses_to_first_term(self) -> None:
        """Assign both courses to term one and verify each course's term."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        term = resources.terms[0]
        for course in resources.courses:
            resources.client.courses.assign_term(
                course_identifier=course["id"],
                term_identifier=term["id"],
            )
        self.wait_for_consistency()
        self.assert_courses_have_term(resources.courses, term)

    def test_92_assign_courses_to_second_term(self) -> None:
        """Move both courses to term two and verify each course's term."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        term = resources.terms[1]
        for course in resources.courses:
            resources.client.courses.assign_term(
                course_identifier=course["id"],
                term_identifier=term["id"],
            )
        self.wait_for_consistency()
        self.assert_courses_have_term(resources.courses, term)

    def test_93_list_courses_assigned_to_second_term(self) -> None:
        """Verify the filtered term-course list contains the two fixture courses."""
        resources = get_test_resources()
        resources.create_base_fixtures()
        term = resources.terms[1]
        self.wait_for_consistency()
        courses = resources.client.courses.list_by_term(
            term_identifier=term["id"]
        )
        course_ids = {course.get("id") for course in courses}
        self.assertTrue(
            {course["id"] for course in resources.courses}.issubset(course_ids)
        )

    def assert_course_has_users(self, course: dict, users: list[dict]) -> None:
        """Assert that a bounded course enrollment list contains all users."""
        enrollments = self.client.enrollments.list_by_course(
            course_identifier=course["id"]
        )
        enrolled_user_ids = {self.enrollment_user_id(item) for item in enrollments}
        self.assertTrue({user["id"] for user in users}.issubset(enrolled_user_ids))

    def assert_node_has_users(self, node: dict, users: list[dict]) -> None:
        """Assert that a bounded node user list contains all users."""
        node_users = self.client.users.list_by_node(node_identifier=node["id"])
        node_user_ids = {self.user_id(item) for item in node_users}
        self.assertTrue({user["id"] for user in users}.issubset(node_user_ids))

    def assert_courses_have_term(self, courses: list[dict], term: dict) -> None:
        """Assert that every supplied course resolves to the supplied term."""
        for course in courses:
            with self.subTest(course_id=course["id"], term_id=term["id"]):
                assigned_term = self.client.terms.get_by_course(
                    course_identifier=course["id"]
                )
                self.assertIsNotNone(assigned_term)
                self.assertEqual(assigned_term["id"], term["id"])

    @property
    def client(self):
        """Return the shared client without recreating resources."""
        return get_test_resources().client

    @staticmethod
    def enrollment_user_id(item: dict) -> str | None:
        """Extract a user primary ID from an enrollment list item."""
        user = item.get("user")
        if isinstance(user, dict):
            return user.get("id") or user.get("userId")
        return item.get("userId") or item.get("id")

    @staticmethod
    def user_id(item: dict) -> str | None:
        """Extract a user primary ID from a node membership list item."""
        return item.get("id") or item.get("userId")

    @staticmethod
    def wait_for_consistency() -> None:
        """Wait for Blackboard's eventual consistency before each verification."""
        time.sleep(2)


if __name__ == "__main__":
    unittest.main()
