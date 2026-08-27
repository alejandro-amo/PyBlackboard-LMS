import unittest
from unittest.mock import Mock

from blackboard_api.facades.courses import CourseFacade
from blackboard_api.facades.enrollments import EnrollmentFacade
from blackboard_api.facades.resources import EnrollmentRoleFacade, NodeFacade
from blackboard_api.facades.terms import TermFacade
from blackboard_api.facades.users import UserFacade


class FacadeDelegationTests(unittest.TestCase):
    def test_course_facade_delegates_resource_and_service_operations(self):
        resource = Mock()
        service = Mock()
        facade = CourseFacade(resource, service)
        facade.list(); facade.iter(); facade.get(course_identifier="C")
        facade.create({"courseId": "C"}); facade.update(course_identifier="C", data={})
        facade.delete(course_identifier="C"); facade.set_available(course_identifier="C")
        facade.set_unavailable(course_identifier="C"); facade.set_disabled(course_identifier="C")
        facade.assign_node(course_identifier="C", node_identifier="N", primary=True)
        facade.unassign_node(course_identifier="C", node_identifier="N")
        facade.list_by_node(node_identifier="N"); facade.iter_by_node(node_identifier="N")
        facade.assign_term(course_identifier="C", term_identifier="T")
        facade.unassign_term(course_identifier="C")
        facade.list_by_term(term_identifier="T")
        facade.get_copy_history(course_identifier="C")
        resource.assign_node.assert_called_once_with(course_identifier="C", node_identifier="N", primary=True)
        service.assign_term.assert_called_once_with(course_identifier="C", term_identifier="T")
        service.list_by_term.assert_called_once_with(term_identifier="T")
        service.get_copy_history.assert_called_once_with(course_identifier="C")

    def test_user_node_term_and_role_facades_delegate_all_public_operations(self):
        user_resource, user_service = Mock(), Mock()
        users = UserFacade(user_resource, user_service)
        users.list(); users.iter(); users.get(user_identifier="U"); users.create({})
        users.update(user_identifier="U", data={}); users.delete(user_identifier="U")
        users.set_available(user_identifier="U"); users.set_unavailable(user_identifier="U")
        users.set_disabled(user_identifier="U")
        users.assign_node(user_identifier="U", node_identifier="N", primary=False)
        users.unassign_node(user_identifier="U", node_identifier="N")
        users.list_by_node(node_identifier="N"); users.iter_by_node(node_identifier="N")
        users.change_username(current_username="old", new_username="new")
        user_service.change_username.assert_called_once_with(current_username="old", new_username="new")

        node_resource = Mock()
        nodes = NodeFacade(node_resource)
        nodes.list(); nodes.iter(); nodes.get(node_identifier="N"); nodes.create({})
        nodes.update(node_identifier="N", data={}); nodes.delete(node_identifier="N")
        nodes.list_by_course(course_identifier="C"); nodes.list_by_user(user_identifier="U")
        node_resource.list_by_user.assert_called_once_with(user_identifier="U")

        term_resource, term_service = Mock(), Mock()
        terms = TermFacade(term_resource, term_service)
        terms.list(); terms.iter(); terms.get(term_identifier="T"); terms.create({})
        terms.update(term_identifier="T", data={}); terms.delete(term_identifier="T")
        terms.get_by_course(course_identifier="C")
        term_service.get_by_course.assert_called_once_with(course_identifier="C")

        role_resource = Mock()
        roles = EnrollmentRoleFacade(role_resource)
        roles.list(); roles.iter()
        role_resource.iter.assert_called_once_with()

    def test_enrollment_facade_delegates_resource_and_service_operations(self):
        resource, service = Mock(), Mock()
        facade = EnrollmentFacade(resource, service)
        facade.list_by_course(course_identifier="C"); facade.iter_by_course(course_identifier="C")
        facade.list_by_user(user_identifier="U"); facade.iter_by_user(user_identifier="U")
        facade.get(course_identifier="C", user_identifier="U")
        facade.create(course_identifier="C", user_identifier="U")
        facade.update(course_identifier="C", user_identifier="U")
        facade.delete(course_identifier="C", user_identifier="U")
        facade.set_available(course_identifier="C", user_identifier="U")
        facade.set_unavailable(course_identifier="C", user_identifier="U")
        facade.set_disabled(course_identifier="C", user_identifier="U")
        facade.find(course_identifier="C", user_identifier="U")
        facade.upsert(course_identifier="C", user_identifier="U")
        facade.ensure_enrolled(course_identifier="C", user_identifier="U")
        facade.change_role(course_identifier="C", user_identifier="U", course_role_id="Instructor")
        facade.set_availability(course_identifier="C", user_identifier="U", available="No")
        facade.activate(course_identifier="C", user_identifier="U")
        facade.deactivate(course_identifier="C", user_identifier="U")
        facade.delete_if_exists(course_identifier="C", user_identifier="U")
        facade.validate_course_role(course_role_id="Student")
        facade.list_for_courses(course_identifiers=["C"]); facade.list_for_users(user_identifiers=["U"])
        facade.enroll_user_in_courses(user_identifier="U", course_identifiers=["C"])
        facade.enroll_users_in_course(course_identifier="C", user_identifiers=["U"])
        resource.create.assert_called_once_with(course_identifier="C", user_identifier="U", course_role_id="Student", availability=None, data_source_id=None, child_course_id=None)
        service.enroll_users_in_course.assert_called_once_with(course_identifier="C", user_identifiers=["U"], course_role_id="Student")


if __name__ == "__main__":
    unittest.main()
