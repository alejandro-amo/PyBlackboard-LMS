import unittest

from blackboard_cli.converters import (
    course_to_row,
    enrollments_to_rows,
    object_to_row,
    users_to_rows,
)


class ConverterTests(unittest.TestCase):
    def test_generic_converter_flattens_nested_data(self):
        self.assertEqual(
            object_to_row({
                "id": "1",
                "name": {"given": "Ana"},
                "roles": ["student", "member"],
            }),
            {"id": "1", "name.given": "Ana", "roles": "student;member"},
        )

    def test_generic_converter_can_exclude_top_level_fields(self):
        self.assertEqual(
            object_to_row(
                {"id": "1", "copyHistory": [{"uuid": "history"}]},
                excluded_fields=("copyHistory",),
            ),
            {"id": "1"},
        )

    def test_specific_converters_preserve_order_and_fields(self):
        users = users_to_rows([{"id": "u1"}, {"id": "u2"}])
        self.assertEqual([user["id"] for user in users], ["u1", "u2"])
        self.assertEqual(course_to_row({"id": "c1", "name": {"text": "Course"}}), {
            "id": "c1", "name.text": "Course"
        })

    def test_iterators_are_consumed_once(self):
        rows = enrollments_to_rows({"id": str(index)} for index in range(2))
        self.assertEqual(rows, [{"id": "0"}, {"id": "1"}])


if __name__ == "__main__":
    unittest.main()
