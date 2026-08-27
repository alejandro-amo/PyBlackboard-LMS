import logging
import unittest
from unittest.mock import Mock, patch

import requests

from blackboard_api.auth import AuthService
from blackboard_api.client import BlackboardAPI
from blackboard_api.errors import AuthenticationError, QuotaExhaustedError, TransportError
from blackboard_api.api_quota import ApiQuotaState


def response(status=200, payload=None, headers=None):
    result = requests.Response()
    result.status_code = status
    result.headers.update(headers or {})
    result._content = requests.models.complexjson.dumps(payload).encode()
    return result


class AuthenticationTests(unittest.TestCase):
    def test_blackboard_api_integrates_auth_transport_and_api_quota(self):
        api = BlackboardAPI(
            url="https://example.test", client_id="id", client_secret="secret"
        )
        session = Mock()
        session.request.side_effect = [
            response(payload={"access_token": "token", "expires_in": 3600}),
            response(headers={
                "X-Rate-Limit-Limit": "100",
                "X-Rate-Limit-Remaining": "99",
            }),
        ]
        api._transport.session = session

        self.assertEqual(api._get_headers()["Authorization"], "Bearer token")
        self.assertEqual(api.api_quota_remaining, 99)

    def test_http_authentication_failure_is_typed(self):
        transport = Mock()
        transport.request.return_value = response(401, {"error": "invalid_client"})
        service = AuthService("https://example.test", "id", "secret", transport)

        with self.assertRaises(AuthenticationError):
            service.request_access_token()

    def test_invalid_json_authentication_failure_is_typed(self):
        transport = Mock()
        result = response(200)
        result._content = b"not-json"
        transport.request.return_value = result
        service = AuthService("https://example.test", "id", "secret", transport)

        with self.assertRaises(AuthenticationError):
            service.request_access_token()

    def test_invalid_expires_in_is_typed(self):
        transport = Mock()
        transport.request.return_value = response(
            payload={"access_token": "token", "expires_in": "invalid"}
        )
        service = AuthService("https://example.test", "id", "secret", transport)

        with self.assertRaises(AuthenticationError):
            service.authenticate(100)

    def test_short_token_gets_limited_expiry_margin(self):
        transport = Mock()
        transport.request.return_value = response(
            payload={"access_token": "token", "expires_in": 30}
        )
        service = AuthService("https://example.test", "id", "secret", transport)

        service.authenticate(100)

        self.assertEqual(service.token_expires_at, 127)

    def test_authentication_reuses_unexpired_token_without_requesting_again(self):
        transport = Mock()
        transport.request.return_value = response(
            payload={"access_token": "token", "expires_in": 3600}
        )
        service = AuthService("https://example.test", "id", "secret", transport)
        self.assertEqual(service.authenticate(100), "token")
        self.assertEqual(service.authenticate(101), "token")
        transport.request.assert_called_once()

    def test_transport_and_missing_token_errors_are_typed(self):
        transport = Mock()
        transport.request.side_effect = TransportError("offline")
        service = AuthService("https://example.test", "id", "secret", transport)
        with self.assertRaises(AuthenticationError):
            service.request_access_token()
        transport.request.side_effect = None
        transport.request.return_value = response(payload={})
        with self.assertRaises(AuthenticationError):
            service.request_access_token()


class ApiQuotaTests(unittest.TestCase):
    def test_missing_remaining_header_preserves_previous_value_and_warns(self):
        state = ApiQuotaState(max_requests_per_day=100, remaining=42)
        result = response(headers={"X-Rate-Limit-Limit": "100"})

        with self.assertLogs("blackboard_api.api_quota", level=logging.WARNING):
            state.update_from_response(result)

        self.assertEqual(state.max_requests_per_day, 100)
        self.assertEqual(state.remaining, 42)

    def test_missing_headers_without_previous_value_does_not_warn(self):
        state = ApiQuotaState()
        with patch("blackboard_api.api_quota.logging.Logger.warning") as warning:
            state.update_from_response(response())
        warning.assert_not_called()

    def test_zero_remaining_is_irrecoverable(self):
        state = ApiQuotaState(remaining=10)
        with self.assertRaises(QuotaExhaustedError):
            state.update_from_response(response(headers={"X-Rate-Limit-Remaining": "0"}))
        self.assertEqual(state.remaining, 0)

    def test_invalid_headers_warn_and_preserve_values(self):
        state = ApiQuotaState(
            max_requests_per_day=100, remaining=42, retry_after=5
        )
        result = response(
            headers={
                "X-Rate-Limit-Limit": "invalid",
                "X-Rate-Limit-Remaining": "invalid",
                "Retry-After": "invalid",
            }
        )

        with self.assertLogs("blackboard_api.api_quota", level=logging.WARNING) as logs:
            state.update_from_response(result)

        self.assertEqual(
            (state.max_requests_per_day, state.remaining, state.retry_after),
            (100, 42, 5),
        )
        self.assertEqual(len(logs.records), 3)


if __name__ == "__main__":
    unittest.main()
