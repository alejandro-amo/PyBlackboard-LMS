import unittest
from unittest.mock import Mock

from blackboard_api.services.users import UserService


class UserServiceTests(unittest.TestCase):
    def test_change_username_validates_both_values_and_requires_a_change(self):
        service = UserService(Mock())
        for current, new in [("", "new"), ("old", ""), ("same", "same")]:
            with self.subTest(current=current, new=new):
                with self.assertRaises(ValueError):
                    service.change_username(current_username=current, new_username=new)

    def test_change_username_uses_a_typed_username_identifier(self):
        users = Mock()
        users.update.return_value = {"userName": "new"}
        result = UserService(users).change_username(
            current_username="old", new_username="new"
        )
        self.assertEqual(result, {"userName": "new"})
        users.update.assert_called_once_with(
            user_identifier="userName:old", data={"userName": "new"}
        )


if __name__ == "__main__":
    unittest.main()
