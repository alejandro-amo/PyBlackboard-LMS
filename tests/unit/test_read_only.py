import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from blackboard_api.client import BlackboardAPI
from blackboard_api.errors import WriteNotEnabledError


class WritePermissionTests(unittest.TestCase):
    def make_client(self, enable_write=False):
        return BlackboardAPI(
            url="https://example.test",
            client_id="id",
            client_secret="secret",
            enable_write=enable_write,
        )

    def test_writes_are_disabled_by_default_with_explicit_credentials(self):
        self.assertFalse(self.make_client().enable_write)

    def test_env_file_is_required_without_explicit_credentials(self):
        with self.assertRaisesRegex(ValueError, "env_file is required"):
            BlackboardAPI()

    def test_mutating_methods_are_blocked_before_transport(self):
        client = self.make_client()
        client._transport.session = Mock()
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            with self.subTest(method=method):
                with self.assertRaises(WriteNotEnabledError):
                    client._request(method, "/resource", headers={})
        client._transport.session.request.assert_not_called()

    def test_writes_are_allowed_when_explicitly_enabled(self):
        client = self.make_client(enable_write=True)
        client._transport.session = Mock()
        response = Mock(status_code=200)
        client._transport.session.request.return_value = response

        client._request("PATCH", "/resource", headers={})

        client._transport.session.request.assert_called_once()

    def test_env_cannot_enable_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(
                "BB_INSTANCE_URL=https://example.test\n"
                "APP_KEY=id\nAPP_SECRET=secret\n"
                "BLACKBOARD_READ_ONLY=false\n",
                encoding="utf-8",
            )
            client = BlackboardAPI(env_file=str(path))
            self.assertFalse(client.enable_write)


if __name__ == "__main__":
    unittest.main()
