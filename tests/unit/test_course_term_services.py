import unittest

from blackboard_api.services.courses import CourseService, TermService


class CourseTermServiceTests(unittest.TestCase):
    def test_assign_term_resolves_external_id_and_updates_course(self):
        class Resource:
            def __init__(self):
                self.calls = []

            def get(self, **kwargs):
                self.calls.append(("get", kwargs))
                return {"id": "_20_1"}

            def update(self, **kwargs):
                self.calls.append(("update", kwargs))
                return kwargs

        courses = Resource()
        terms = Resource()
        result = CourseService(courses, terms).assign_term(
            course_identifier="courseId:C1", term_identifier="externalId:T1"
        )
        self.assertEqual(result["data"], {"termId": "_20_1"})
        self.assertEqual(terms.calls[0][1], {"term_identifier": "externalId:T1"})

    def test_get_by_course_returns_term_or_none(self):
        class Courses:
            def get(self, **kwargs):
                return {"termId": "_20_1"}

        class Terms:
            def get(self, **kwargs):
                return {"id": kwargs["term_identifier"]}

        result = TermService(Courses(), Terms()).get_by_course(
            course_identifier="_1_1"
        )
        self.assertEqual(result, {"id": "_20_1"})

    def test_assign_term_requires_the_term_primary_id(self):
        class Terms:
            def get(self, **kwargs):
                return {"externalId": "T1"}

        with self.assertRaisesRegex(ValueError, "primary ID"):
            CourseService(object(), Terms()).assign_term(
                course_identifier="C", term_identifier="T"
            )

    def test_list_by_term_resolves_the_term_before_filtering_courses(self):
        class Courses:
            def _list_by_term_primary_id(self, *, term_id):
                return [{"id": "_1_1", "termId": term_id}]

        class Terms:
            def get(self, **kwargs):
                self.identifier = kwargs["term_identifier"]
                return {"id": "_20_1"}

        terms = Terms()
        result = CourseService(Courses(), terms).list_by_term(
            term_identifier="externalId:T1"
        )
        self.assertEqual(terms.identifier, "externalId:T1")
        self.assertEqual(result, [{"id": "_1_1", "termId": "_20_1"}])

    def test_get_copy_history_returns_the_course_value(self):
        class Courses:
            def get(self, **kwargs):
                self.identifier = kwargs["course_identifier"]
                return {"copyHistory": [{"uuid": "history-uuid"}]}

        courses = Courses()
        result = CourseService(courses, object()).get_copy_history(
            course_identifier="courseId:C1"
        )
        self.assertEqual(courses.identifier, "courseId:C1")
        self.assertEqual(result, [{"uuid": "history-uuid"}])

    def test_unassign_term_and_missing_term_are_handled_without_extra_requests(self):
        class Courses:
            def __init__(self, term_id=None):
                self.term_id = term_id
                self.calls = []

            def get(self, **kwargs):
                return {"termId": self.term_id}

            def update(self, **kwargs):
                self.calls.append(kwargs)
                return kwargs

        courses = Courses()
        self.assertEqual(
            CourseService(courses, object()).unassign_term(course_identifier="C"),
            {"course_identifier": "C", "data": {"termId": None}},
        )
        self.assertIsNone(TermService(courses, object()).get_by_course(course_identifier="C"))


if __name__ == "__main__":
    unittest.main()
