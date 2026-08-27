import unittest

from blackboard_api.identifiers import (
    IdentifierPolicy,
    InvalidIdentifierError,
    validate_identifier,
)
from blackboard_api.client import BlackboardAPI
from blackboard_api.resources.courses import CourseResource
from blackboard_api.resources.enrollments import EnrollmentResource
from blackboard_api.resources.nodes import NodeResource
from blackboard_api.resources.users import UserResource
from blackboard_api.resources.terms import TermResource
from blackboard_api.errors import ResponseFormatError


class FakeClient:
    def __init__(self, pages=None):
        self.calls = []
        self.pages = pages or {}

    def _request_json(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return self.pages.get(path, {})

    def _request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return object()

    def _iter_paginated(self, path):
        while path:
            data = self.pages.get(path, {"results": []})
            yield from data.get("results", [])
            path = data.get("paging", {}).get("nextPage")


class ResourceTests(unittest.TestCase):
    def test_identifier_policy_accepts_primary_and_explicit_types(self):
        policy = IdentifierPolicy(frozenset({"externalId", "uuid"}))
        self.assertEqual(
            validate_identifier("_1_1", name="identifier", policy=policy),
            "_1_1",
        )
        self.assertEqual(
            validate_identifier(
                "externalId:EXT-1", name="identifier", policy=policy
            ),
            "externalId:EXT-1",
        )

    def test_identifier_policy_rejects_unknown_explicit_type(self):
        policy = IdentifierPolicy(frozenset({"externalId"}))
        with self.assertRaises(InvalidIdentifierError):
            validate_identifier("courseId:C1", name="identifier", policy=policy)

    def test_identifier_policy_can_require_explicit_type(self):
        policy = IdentifierPolicy(frozenset({"externalId"}), primary_allowed=False)
        with self.assertRaises(InvalidIdentifierError):
            validate_identifier("_1_1", name="identifier", policy=policy)

    def test_course_get_accepts_explicit_id_types_and_encodes_path(self):
        client = FakeClient()
        resource = CourseResource(client)
        resource.get(course_identifier="courseId:COURSE-1")
        self.assertEqual(client.calls[0][1], "/learn/api/public/v2/courses/courseId:COURSE-1")

        resource.get(course_identifier="externalId:course@example.com")
        self.assertEqual(client.calls[1][1], "/learn/api/public/v2/courses/externalId:course%40example.com")

    def test_invalid_identifier_is_rejected_before_request(self):
        client = FakeClient()
        with self.assertRaises(InvalidIdentifierError):
            CourseResource(client).get(course_identifier="userName:someone")
        self.assertEqual(client.calls, [])

    def test_user_create_requires_dict_data(self):
        client = FakeClient()
        with self.assertRaises(ValueError):
            UserResource(client).create(None)
        self.assertEqual(client.calls, [])

    def test_create_rejects_blackboard_generated_identifiers(self):
        resources = (
            (CourseResource, {"courseId": "C-1", "name": "Course"}),
            (UserResource, {
                "userName": "user", "password": "secret",
                "name": {"given": "User", "family": "Test"},
            }),
            (TermResource, {"externalId": "T-1", "name": "Term"}),
            (NodeResource, {"title": "Node"}),
        )
        for resource_type, data in resources:
            with self.subTest(resource=resource_type.__name__):
                client = FakeClient()
                with self.assertRaisesRegex(ValueError, "id"):
                    resource_type(client).create({**data, "id": "_1_1"})
                with self.assertRaisesRegex(ValueError, "uuid"):
                    resource_type(client).create({**data, "uuid": "u-1"})
                self.assertEqual(client.calls, [])

    def test_term_crud_uses_v1_and_typed_identifiers(self):
        client = FakeClient()
        resource = TermResource(client)
        resource.get(term_identifier="externalId:TERM-1")
        resource.create({"externalId": "TERM-1", "name": "Term"})
        resource.update(
            term_identifier="_10_1", data={"name": "Updated term"}
        )
        resource.delete(term_identifier="externalId:TERM-1")
        self.assertEqual(
            [(method, path) for method, path, _ in client.calls],
            [
                ("GET", "/learn/api/public/v1/terms/externalId:TERM-1"),
                ("POST", "/learn/api/public/v1/terms"),
                ("PATCH", "/learn/api/public/v1/terms/_10_1"),
                ("DELETE", "/learn/api/public/v1/terms/externalId:TERM-1"),
            ],
        )

    def test_node_primary_flag_requires_boolean(self):
        client = FakeClient()
        with self.assertRaises(TypeError):
            CourseResource(client).assign_node(
                course_identifier="courseId:COURSE-1", node_identifier="externalId:NODE-1", primary="yes"
            )

    def test_pagination_combines_all_pages(self):
        client = FakeClient({
            "/collection": {"results": [{"id": 1}], "paging": {"nextPage": "/collection?page=2"}},
            "/collection?page=2": {"results": [{"id": 2}], "paging": {}},
        })
        self.assertEqual(list(client._iter_paginated("/collection")), [{"id": 1}, {"id": 2}])

    def test_invalid_json_response_is_rejected(self):
        class InvalidJsonResponse:
            def json(self):
                raise ValueError("invalid json")

        client = object.__new__(BlackboardAPI)
        client._request = lambda method, path, **kwargs: InvalidJsonResponse()
        with self.assertRaises(ResponseFormatError):
            client._request_json("GET", "/collection")

    def test_invalid_collection_results_are_rejected(self):
        class InvalidCollectionClient(FakeClient):
            def _request_json(self, method, path, **kwargs):
                return {"results": {}, "paging": {}}

        with self.assertRaises(ResponseFormatError):
            list(BlackboardAPI._iter_paginated(InvalidCollectionClient(), "/collection"))

    def test_resource_iterators_do_not_accumulate(self):
        client = FakeClient({"/learn/api/public/v1/users": {"results": [{"id": "u1"}]}})
        self.assertEqual(list(UserResource(client).iter()), [{"id": "u1"}])
        self.assertEqual(client.calls, [])

    def test_enrollment_routes_are_distinct_and_keyword_only(self):
        client = FakeClient({
            "/learn/api/public/v1/courses/courseId:COURSE-1/users": {"results": [{"id": "e1"}]},
            "/learn/api/public/v1/users/uuid:u-1/courses": {"results": [{"id": "e2"}]},
        })
        resource = EnrollmentResource(client)
        self.assertEqual(resource.list_by_course(course_identifier="courseId:COURSE-1"), [{"id": "e1"}])
        self.assertEqual(resource.list_by_user(user_identifier="uuid:u-1"), [{"id": "e2"}])
        self.assertEqual(client.calls, [])

    def test_create_sends_expected_enrollment_body(self):
        client = FakeClient()
        EnrollmentResource(client).create(
            course_identifier="courseId:COURSE-1",
            user_identifier="userName:a@example.com",
            course_role_id="Instructor",
        )
        method, path, kwargs = client.calls[0]
        self.assertEqual((method, path), ("PUT", "/learn/api/public/v1/courses/courseId:COURSE-1/users/userName:a%40example.com"))
        self.assertEqual(kwargs["json"]["courseRoleId"], "Instructor")

    def test_availability_convenience_methods_use_patch(self):
        client = FakeClient()
        CourseResource(client).set_available(course_identifier="courseId:C1")
        UserResource(client).set_unavailable(user_identifier="userName:u")
        EnrollmentResource(client).set_disabled(
            course_identifier="courseId:C1",
            user_identifier="userName:u",
        )
        self.assertEqual(
            [call[0] for call in client.calls], ["PATCH", "PATCH", "PATCH"]
        )
        self.assertEqual(
            client.calls[0][2]["json"],
            {"availability": {"available": "Yes"}},
        )
        self.assertEqual(
            client.calls[1][2]["json"],
            {"availability": {"available": "No"}},
        )
        self.assertEqual(
            client.calls[2][2]["json"],
            {"availability": {"available": "Disabled"}},
        )


if __name__ == "__main__":
    unittest.main()
