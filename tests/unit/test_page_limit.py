import unittest

from blackboard_api import BlackboardAPI


class PageLimitTests(unittest.TestCase):
    def make_api(self):
        return BlackboardAPI(
            url="https://blackboard.example.test",
            client_id="client",
            client_secret="secret",
        )

    def test_default_results_per_page_is_one_hundred(self):
        api = self.make_api()

        self.assertEqual(api.results_per_page, 100)
        self.assertEqual(
            api._with_results_per_page("/learn/api/public/v1/courses"),
            "/learn/api/public/v1/courses?limit=100",
        )

    def test_results_per_page_can_change_after_initialization(self):
        api = self.make_api()
        api.results_per_page = 250

        self.assertEqual(
            api._with_results_per_page("/learn/api/public/v1/courses"),
            "/learn/api/public/v1/courses?limit=250",
        )

    def test_explicit_limit_is_not_overwritten(self):
        api = self.make_api()
        api.results_per_page = 250

        self.assertEqual(
            api._with_results_per_page("/learn/api/public/v1/users?limit=50"),
            "/learn/api/public/v1/users?limit=50",
        )

    def test_results_per_page_must_be_positive_integer(self):
        api = self.make_api()

        with self.assertRaises(ValueError):
            api.results_per_page = 0
        with self.assertRaises(ValueError):
            api.results_per_page = True


if __name__ == "__main__":
    unittest.main()
