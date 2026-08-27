import unittest

from blackboard_api.resources.courses import CourseResource
from blackboard_api.resources.enrollment_roles import EnrollmentRoleResource
from blackboard_api.resources.enrollments import EnrollmentResource
from blackboard_api.resources.nodes import NodeResource
from blackboard_api.resources.users import UserResource


class RecordingClient:
    def __init__(self):
        self.calls = []

    def _request_json(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return {"method": method, "path": path}

    def _request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))

    def _iter_paginated(self, path):
        self.calls.append(("ITER", path, {}))
        yield {"path": path}


class ResourceCrudOperationTests(unittest.TestCase):
    def test_course_crud_and_node_relations_build_documented_requests(self):
        client = RecordingClient()
        courses = CourseResource(client)

        self.assertEqual(courses.list(), [{"path": "/learn/api/public/v2/courses"}])
        self.assertEqual(
            list(courses.iter_by_node(node_identifier="externalId:Faculty A")),
            [{
                "path": (
                    "/learn/api/public/v1/institutionalHierarchy/nodes/"
                    "externalId:Faculty%20A/courses"
                )
            }],
        )
        courses.create({"courseId": "C1", "name": "Course"})
        courses.update(course_identifier="uuid:course-uuid", data={"name": "New"})
        courses.delete(course_identifier="externalId:C1")
        courses.assign_node(
            course_identifier="courseId:C1",
            node_identifier="externalId:N1",
            primary=True,
        )
        courses.unassign_node(
            course_identifier="courseId:C1", node_identifier="externalId:N1"
        )

        self.assertEqual(client.calls[0][:2], ("ITER", "/learn/api/public/v2/courses"))
        self.assertEqual(client.calls[2][0:2], ("POST", "/learn/api/public/v2/courses"))
        self.assertEqual(
            client.calls[3][0:2],
            ("PATCH", "/learn/api/public/v2/courses/uuid:course-uuid"),
        )
        self.assertEqual(
            client.calls[5][2]["json"], {"isPrimary": True},
        )
        self.assertEqual(client.calls[6][0], "DELETE")

    def test_user_crud_availability_and_node_relations_build_requests(self):
        client = RecordingClient()
        users = UserResource(client)

        self.assertEqual(users.list(), [{"path": "/learn/api/public/v1/users"}])
        self.assertEqual(
            users.list_by_node(node_identifier="externalId:N 1"),
            [{
                "path": (
                    "/learn/api/public/v1/institutionalHierarchy/nodes/"
                    "externalId:N%201/users"
                )
            }],
        )
        users.create({"userName": "u", "name": {"given": "U"}})
        users.update(user_identifier="uuid:u-1", data={"contact": {}})
        users.set_available(user_identifier="userName:u")
        users.set_unavailable(user_identifier="userName:u")
        users.set_disabled(user_identifier="userName:u")
        users.delete(user_identifier="externalId:U1")
        users.assign_node(
            user_identifier="userName:u", node_identifier="externalId:N1"
        )
        users.unassign_node(
            user_identifier="userName:u", node_identifier="externalId:N1"
        )

        patches = [call for call in client.calls if call[0] == "PATCH"]
        self.assertEqual(len(patches), 4)
        self.assertEqual(patches[1][2]["json"], {"availability": {"available": "Yes"}})
        self.assertEqual(client.calls[-2][2]["json"], {})
        self.assertEqual(client.calls[-1][0], "DELETE")

    def test_node_crud_and_relationship_lists_build_requests(self):
        client = RecordingClient()
        nodes = NodeResource(client)

        self.assertEqual(nodes.list(), [{"path": "/learn/api/public/v1/institutionalHierarchy/nodes"}])
        nodes.get(node_identifier="externalId:N 1")
        nodes.create({"externalId": "N1", "title": "Node"})
        nodes.update(node_identifier="_1_1", data={"title": "New"})
        nodes.delete(node_identifier="externalId:N1")
        self.assertEqual(nodes.list_by_course(course_identifier="courseId:C1"), [{"path": "/learn/api/public/v1/courses/courseId:C1/nodes"}])
        self.assertEqual(nodes.list_by_user(user_identifier="userName:u@example.com"), [{"path": "/learn/api/public/v1/users/userName:u%40example.com/nodes"}])

        self.assertEqual(
            client.calls[1][0:2],
            ("GET", "/learn/api/public/v1/institutionalHierarchy/nodes/externalId:N%201"),
        )
        self.assertEqual(client.calls[3][0], "PATCH")
        self.assertEqual(client.calls[4][0], "DELETE")

    def test_enrollment_update_rejects_empty_body_and_supports_optional_fields(self):
        client = RecordingClient()
        enrollments = EnrollmentResource(client)
        with self.assertRaises(ValueError):
            enrollments.update(course_identifier="courseId:C1", user_identifier="userName:u")
        enrollments.update(
            course_identifier="courseId:C1",
            user_identifier="userName:u",
            course_role_id="Instructor",
            data_source_id="DS1",
            child_course_id="_2_1",
        )
        self.assertEqual(client.calls[0][2]["json"], {
            "courseRoleId": "Instructor",
            "dataSourceId": "DS1",
            "childCourseId": "_2_1",
        })
        enrollments.delete(course_identifier="courseId:C1", user_identifier="userName:u")
        self.assertEqual(client.calls[-1][0], "DELETE")

    def test_enrollment_roles_list_and_iter_use_the_course_roles_endpoint(self):
        client = RecordingClient()
        roles = EnrollmentRoleResource(client)
        self.assertEqual(roles.list(), [{"path": "/learn/api/public/v1/courseRoles"}])
        self.assertEqual(
            list(roles.iter()), [{"path": "/learn/api/public/v1/courseRoles"}]
        )


if __name__ == "__main__":
    unittest.main()
