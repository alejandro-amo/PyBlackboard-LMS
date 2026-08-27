import unittest
from unittest.mock import Mock, patch

import requests

from blackboard_api.errors import QuotaExhaustedError, TransportError
from blackboard_api.api_quota import ApiQuotaState
from blackboard_api.transport import Transport, _parse_retry_after, _retry_delay


def response(status, headers=None):
    result = requests.Response()
    result.status_code = status
    result.headers.update(headers or {})
    result.url = "https://example.test"
    return result


class TransportTests(unittest.TestCase):
    def test_retries_transient_status_with_exponential_jitter(self):
        session = Mock()
        session.request.side_effect = [response(503), response(200)]
        transport = Transport(session=session)

        with patch("blackboard_api.transport.random.uniform", return_value=0.25) as jitter, \
                patch("blackboard_api.transport.time.sleep"):
            result = transport.request("GET", "https://example.test")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(session.request.call_count, 2)
        jitter.assert_called_once_with(0, 5.0)

    def test_honours_short_retry_after(self):
        session = Mock()
        session.request.side_effect = [response(429, {"Retry-After": "3"}), response(200)]
        transport = Transport(session=session)

        with patch("blackboard_api.transport.time.sleep") as sleep:
            transport.request("GET", "https://example.test")

        sleep.assert_called_once_with(3.0)

    def test_rejects_retry_after_over_cap(self):
        result = response(503, {"Retry-After": "7200"})
        with self.assertRaises(TransportError):
            _retry_delay(result, 1, 5)

    def test_retries_transient_network_errors(self):
        session = Mock()
        session.request.side_effect = [requests.ConnectionError(), response(200)]
        transport = Transport(session=session)

        with patch("blackboard_api.transport.time.sleep"):
            result = transport.request("GET", "https://example.test")

        self.assertEqual(result.status_code, 200)

    def test_non_transient_network_error_is_wrapped_without_retry(self):
        session = Mock()
        session.request.side_effect = requests.exceptions.HTTPError("bad response")
        transport = Transport(session=session)

        with self.assertRaises(TransportError):
            transport.request("GET", "https://example.test")
        session.request.assert_called_once()

    def test_known_zero_quota_blocks_request_before_network(self):
        session = Mock()
        transport = Transport(session=session, api_quota=ApiQuotaState(remaining=0))

        with self.assertRaises(QuotaExhaustedError):
            transport.request("GET", "https://example.test")
        session.request.assert_not_called()

    def test_timeout_is_forwarded_by_default(self):
        session = Mock()
        session.request.return_value = response(200)
        transport = Transport(session=session, timeout=(2, 7))

        transport.request("GET", "https://example.test")

        self.assertEqual(session.request.call_args.kwargs["timeout"], (2, 7))

    def test_explicit_timeout_takes_precedence(self):
        session = Mock()
        session.request.return_value = response(200)
        transport = Transport(session=session, timeout=(2, 7))

        transport.request("GET", "https://example.test", timeout=11)

        self.assertEqual(session.request.call_args.kwargs["timeout"], 11)

    def test_constructor_and_request_validate_retry_configuration(self):
        with self.assertRaises(ValueError):
            Transport(max_retries=-1)
        transport = Transport(session=Mock())
        with self.assertRaises(ValueError):
            transport.request("GET", "https://example.test", max_retries=-1)
        with self.assertRaises(ValueError):
            transport.request("GET", "https://example.test", backoff=-1)

    def test_final_transient_response_is_returned_without_an_extra_retry(self):
        session = Mock()
        session.request.return_value = response(503)
        transport = Transport(session=session, max_retries=0)
        self.assertEqual(transport.request("GET", "https://example.test").status_code, 503)
        session.request.assert_called_once()

    def test_last_network_failure_is_wrapped_after_retry_limit(self):
        session = Mock()
        session.request.side_effect = requests.ConnectionError()
        transport = Transport(session=session, max_retries=0)
        with self.assertRaises(TransportError):
            transport.request("GET", "https://example.test")
        session.request.assert_called_once()

    def test_retry_after_parser_handles_invalid_and_http_date_values(self):
        self.assertIsNone(_parse_retry_after("not-a-delay"))
        self.assertIsInstance(
            _parse_retry_after("Thu, 01 Jan 1970 00:00:00 GMT"), float
        )


if __name__ == "__main__":
    unittest.main()
