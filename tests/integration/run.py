"""Run the integration suite with console and persistent logging."""

from __future__ import annotations

import argparse
import logging
import sys
import unittest
from datetime import datetime
from pathlib import Path

from blackboard_cli.encoding import force_utf8_standard_streams

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_DIR = Path(__file__).resolve().parent
LOG_DIRECTORY = PROJECT_ROOT / "data" / "test-artifacts" / "logs"


def parse_arguments() -> argparse.Namespace:
    """Return runner-specific arguments."""
    parser = argparse.ArgumentParser(
        description="Run Blackboard integration tests against .env.test.local."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        type=str.upper,
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        help="Minimum level written to standard output and the log file.",
    )
    return parser.parse_args()


def configure_logging(level_name: str) -> Path:
    """Configure process logging and return the created log file path."""
    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = LOG_DIRECTORY / f"integration-{timestamp}.log"
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    handlers = (
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_path, encoding="utf-8"),
    )
    for handler in handlers:
        handler.setFormatter(formatter)
    logging.basicConfig(
        level=getattr(logging, level_name),
        handlers=handlers,
        force=True,
    )
    logging.getLogger(__name__).info("Integration log file: %s", log_path)
    return log_path


def main() -> int:
    """Run all integration tests and return a process-compatible exit code."""
    force_utf8_standard_streams()
    arguments = parse_arguments()
    log_path = configure_logging(arguments.log_level)
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(INTEGRATION_DIR),
        pattern="test_*.py",
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    logging.getLogger(__name__).info(
        "Integration suite finished: ran=%s failures=%s errors=%s log=%s",
        result.testsRun,
        len(result.failures),
        len(result.errors),
        log_path,
    )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
