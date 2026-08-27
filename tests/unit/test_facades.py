import unittest
import inspect

from blackboard_api.client import BlackboardAPI
from blackboard_api.facades.enrollments import EnrollmentFacade


class FacadeTests(unittest.TestCase):
    def test_client_exposes_resource_and_service_operations_together(self):
        client = BlackboardAPI(
            url="https://example.test", client_id="id", client_secret="secret"
        )

        self.assertTrue(callable(client.courses.list))
        self.assertTrue(callable(client.users.get))
        self.assertTrue(callable(client.users.change_username))
        self.assertTrue(callable(client.nodes.list))
        self.assertTrue(callable(client.enrollment_roles.list))
        self.assertTrue(callable(client.terms.list))
        self.assertTrue(callable(client.courses.assign_term))
        self.assertTrue(callable(client.courses.unassign_term))
        self.assertTrue(callable(client.terms.get_by_course))
        self.assertTrue(callable(client.enrollments.list_by_course))
        self.assertTrue(callable(client.enrollments.upsert))
        self.assertIs(client.enrollments._service, client._enrollment_service)

    def test_enrollment_facade_has_no_variadic_public_methods(self):
        for name, method in inspect.getmembers(EnrollmentFacade, inspect.isfunction):
            if name.startswith("_"):
                continue
            parameters = inspect.signature(method).parameters.values()
            self.assertNotIn(
                inspect.Parameter.VAR_KEYWORD,
                {parameter.kind for parameter in parameters},
                name,
            )


class UserServiceFacadeTests(unittest.TestCase):
    def test_change_username_updates_using_typed_username_identifier(self):
        class Users:
            def __init__(self):
                self.calls = []

            def update(self, **kwargs):
                self.calls.append(("update", kwargs))
                return {"id": "_12_1", "userName": "XYZ"}

        from blackboard_api.facades.users import UserFacade
        from blackboard_api.services.users import UserService

        users = Users()
        result = UserFacade(users, UserService(users)).change_username(
            current_username="ABC", new_username="XYZ"
        )
        self.assertEqual(result["userName"], "XYZ")
        self.assertEqual(users.calls[0][1], {
            "user_identifier": "userName:ABC",
            "data": {"userName": "XYZ"},
        })


if __name__ == "__main__":
    unittest.main()
