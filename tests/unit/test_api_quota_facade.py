import unittest
from unittest.mock import patch

from blackboard_api import BlackboardAPI
from blackboard_api.facades.api_quota import ApiQuotaFacade


class ApiQuotaFacadeTests(unittest.TestCase):
    def test_get_returns_remaining_and_daily_maximum(self):
        facade = ApiQuotaFacade(
            lambda: {"remaining": 1234, "max_requests_per_day": 10000},
        )

        self.assertEqual(
            facade.get(),
            {"remaining": 1234, "max_requests_per_day": 10000},
        )

    def test_get_preserves_unknown_values_as_none(self):
        facade = ApiQuotaFacade(
            lambda: {"remaining": None, "max_requests_per_day": None},
        )

        self.assertEqual(
            facade.get(),
            {"remaining": None, "max_requests_per_day": None},
        )

    def test_api_exposes_api_quota_facade(self):
        api = BlackboardAPI(
            url="https://blackboard.example.test",
            client_id="client",
            client_secret="secret",
        )

        with patch.object(api, "_update_api_quota") as update:
            self.assertEqual(
                api.api_quota.get(),
                {"remaining": None, "max_requests_per_day": None},
            )
        update.assert_called_once_with()

    def test_api_quota_facade_probes_once_when_unknown(self):
        api = BlackboardAPI(
            url="https://blackboard.example.test",
            client_id="client",
            client_secret="secret",
        )

        def probe():
            api._api_quota.max_requests_per_day = 10000
            api._api_quota.remaining = 1234

        with patch.object(api, "_update_api_quota", side_effect=probe) as update:
            self.assertEqual(
                api.api_quota.get(),
                {"remaining": 1234, "max_requests_per_day": 10000},
            )
            self.assertEqual(
                api.api_quota.get(),
                {"remaining": 1234, "max_requests_per_day": 10000},
            )

        update.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
