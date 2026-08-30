import unittest

from blackboard_api.errors import NotFoundError
from blackboard_api.services.enrollments import EnrollmentService


class FakeEnrollments:
    def __init__(self, current=None):
        self.current = current
        self.calls = []

    def get(self, **kwargs):
        if self.current is None:
            raise NotFoundError("missing")
        return self.current

    def create(self, **kwargs):
        self.calls.append(("create", kwargs))
        return {**kwargs, "courseRoleId": kwargs["course_role_id"]}

    def update(self, **kwargs):
        self.calls.append(("update", kwargs))
        return kwargs

    def delete(self, **kwargs):
        self.calls.append(("delete", kwargs))

    def list_by_course(self, **kwargs):
        return [{"course": kwargs["course_identifier"]}]

    def list_by_user(self, **kwargs):
        return [{"user": kwargs["user_identifier"]}]


class FakeClient:
    def __init__(self, current=None):
        self.enrollments = FakeEnrollments(current)
        self.users = object()
        self.courses = object()
        self.enrollment_roles = FakeRoles()


class FakeRoles:
    def __init__(self):
        self.calls = 0

    def list(self):
        self.calls += 1
        return [{"id": "Student"}, {"id": "Instructor"}]


class EnrollmentServiceTests(unittest.TestCase):
    def test_upsert_creates_when_missing(self):
        client = FakeClient()
        service = EnrollmentService(client.enrollments, client.enrollment_roles)
        result = service.upsert(
            course_identifier="courseId:C1", user_identifier="userName:U"
        )
        self.assertEqual(result["courseRoleId"], "Student")
        self.assertEqual(service.enrollments.calls[0][0], "create")

    def test_upsert_updates_only_changed_fields(self):
        client = FakeClient({
            "courseRoleId": "Student",
            "availability": {"available": "Yes"},
        })
        service = EnrollmentService(client.enrollments, client.enrollment_roles)
        service.upsert(
            course_identifier="courseId:C1", user_identifier="userName:U",
            course_role_id="Instructor",
        )
        self.assertEqual(client.enrollments.calls[0][1]["course_role_id"], "Instructor")
        self.assertNotIn("availability", client.enrollments.calls[0][1])

    def test_set_availability_rejects_invalid_value(self):
        client = FakeClient()
        service = EnrollmentService(client.enrollments, client.enrollment_roles)
        with self.assertRaises(ValueError):
            service.set_availability(
                course_identifier="C1", user_identifier="U", available="Maybe"
            )

    def test_set_availability_accepts_disabled(self):
        client = FakeClient()
        service = EnrollmentService(client.enrollments, client.enrollment_roles)
        service.set_availability(
            course_identifier="C1", user_identifier="U", available="Disabled"
        )
        self.assertEqual(
            client.enrollments.calls[0][1]["availability"],
            {"available": "Disabled"},
        )

    def test_course_roles_are_loaded_once_and_cached(self):
        client = FakeClient()
        service = EnrollmentService(client.enrollments, client.enrollment_roles)

        self.assertEqual(service.validate_course_role(course_role_id="Student")["id"], "Student")
        self.assertEqual(service.validate_course_role(course_role_id="Instructor")["id"], "Instructor")
        self.assertEqual(client.enrollment_roles.calls, 1)

    def test_find_returns_none_only_for_not_found(self):
        client = FakeClient()
        service = EnrollmentService(client.enrollments, client.enrollment_roles)
        self.assertIsNone(
            service.find(course_identifier="courseId:C1", user_identifier="userName:U")
        )

    def test_upsert_returns_existing_enrollment_when_it_already_matches(self):
        current = {
            "courseRoleId": "Student",
            "availability": {"available": "Yes"},
        }
        client = FakeClient(current)
        service = EnrollmentService(client.enrollments, client.enrollment_roles)
        self.assertIs(
            service.upsert(course_identifier="courseId:C1", user_identifier="userName:U"),
            current,
        )
        self.assertEqual(client.enrollments.calls, [])

    def test_change_role_activation_and_deletion_delegate_correctly(self):
        client = FakeClient({"courseRoleId": "Student"})
        service = EnrollmentService(client.enrollments, client.enrollment_roles)
        service.upsert(
            course_identifier="C", user_identifier="U", availability={"available": "No"}
        )
        service.change_role(course_identifier="C", user_identifier="U", course_role_id="Instructor")
        service.activate(course_identifier="C", user_identifier="U")
        service.deactivate(course_identifier="C", user_identifier="U")
        self.assertTrue(service.delete_if_exists(course_identifier="C", user_identifier="U"))
        self.assertEqual(
            [name for name, _ in client.enrollments.calls],
            ["update", "update", "update", "update", "delete"],
        )

    def test_delete_if_exists_returns_false_when_the_enrollment_is_missing(self):
        client = FakeClient()
        service = EnrollmentService(client.enrollments, client.enrollment_roles)
        self.assertFalse(service.delete_if_exists(course_identifier="C", user_identifier="U"))
        self.assertEqual(client.enrollments.calls, [])

    def test_role_validation_rejects_unknown_role_and_invalid_availability(self):
        client = FakeClient()
        service = EnrollmentService(client.enrollments, client.enrollment_roles)
        with self.assertRaisesRegex(ValueError, "Unknown course role"):
            service.validate_course_role(course_role_id="NotARole")
        with self.assertRaisesRegex(ValueError, "availability"):
            service.upsert(
                course_identifier="C", user_identifier="U", availability={"available": "Maybe"}
            )

    def test_multiple_enrollment_helpers_preserve_order_and_remove_duplicates(self):
        client = FakeClient()
        service = EnrollmentService(client.enrollments, client.enrollment_roles)
        self.assertEqual(
            service.list_for_courses(course_identifiers=["C1", "C2", "C1"]),
            [{"course": "C1"}, {"course": "C2"}],
        )
        self.assertEqual(
            service.list_for_users(user_identifiers=["U1", "U2", "U1"]),
            [{"user": "U1"}, {"user": "U2"}],
        )
        self.assertEqual(
            service.enroll_user_in_courses(
                user_identifier="U", course_identifiers=["C1", "C2"]
            ),
            [
                {"course_identifier": "C1", "user_identifier": "U", "course_role_id": "Student", "availability": None, "data_source_id": None, "child_course_id": None, "courseRoleId": "Student"},
                {"course_identifier": "C2", "user_identifier": "U", "course_role_id": "Student", "availability": None, "data_source_id": None, "child_course_id": None, "courseRoleId": "Student"},
            ],
        )
        self.assertEqual(
            len(service.enroll_users_in_course(
                course_identifier="C", user_identifiers=["U1", "U2"]
            )),
            2,
        )


if __name__ == "__main__":
    unittest.main()
