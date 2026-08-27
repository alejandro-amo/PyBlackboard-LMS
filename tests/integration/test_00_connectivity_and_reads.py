"""Connectivity and API quota tests for the Blackboard test tenant."""

from __future__ import annotations

import logging
import unittest
from pathlib import Path

from blackboard_api import BlackboardAPI
from blackboard_api.config import api_config_from_environment


TEST_ENV_FILE = Path(__file__).resolve().parents[2] / ".env.test.local"
logger = logging.getLogger(__name__)


class ConnectivityTests(unittest.TestCase):
    """Verify authentication and the API quota probe only."""

    @classmethod
    def setUpClass(cls) -> None:
        try:
            api_config_from_environment(TEST_ENV_FILE)
        except (FileNotFoundError, ValueError) as exc:
            raise RuntimeError(
                "Live integration tests require a valid .env.test.local file"
            ) from exc
        cls.client = BlackboardAPI(env_file=str(TEST_ENV_FILE))

    def test_00_api_connectivity_and_quota(self) -> None:
        """Authenticate and return the quota information reported by Blackboard."""
        quota = self.client.api_quota.get()
        self.assertEqual(set(quota), {"remaining", "max_requests_per_day"})
        remaining = quota["remaining"]
        if remaining is not None and remaining < 1000:
            logger.warning(
                "Fewer than 1,000 API requests remain in the daily quota. "
                "Before running the complete integration test plan, make "
                "sure a large number of requests remain, or wait for the "
                "quota to reset the following day."
            )


if __name__ == "__main__":
    unittest.main()
