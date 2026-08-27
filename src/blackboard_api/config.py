import os
from pathlib import Path
from typing import Any

DEFAULT_CONNECT_TIMEOUT_SECONDS = 10
DEFAULT_READ_TIMEOUT_SECONDS = 60


def load_environment(path: str | Path) -> dict[str, str]:
    env_path = Path(path)
    if not env_path.is_file():
        raise FileNotFoundError(f"Environment file does not exist: {env_path}")
    values = {}
    for line_number, raw_line in enumerate(env_path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid format in {env_path}, line {line_number}")
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _positive_int(value: Any, name: str, default: int) -> int:
    value = default if value in (None, "") else value
    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def api_config_from_environment(path: str | Path) -> dict[str, Any]:
    values = load_environment(path)
    required = {
        "BB_INSTANCE_URL": values.get("BB_INSTANCE_URL"),
        "APP_KEY": values.get("APP_KEY"),
        "APP_SECRET": values.get("APP_SECRET"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise ValueError("Missing required environment variables: " + ", ".join(missing))
    return {
        "url": required["BB_INSTANCE_URL"],
        "client_id": required["APP_KEY"],
        "client_secret": required["APP_SECRET"],
        "connect_timeout": _positive_int(values.get("BB_REQUEST_CONNECT_TIMEOUT") or os.environ.get("BB_REQUEST_CONNECT_TIMEOUT"), "connect timeout", DEFAULT_CONNECT_TIMEOUT_SECONDS),
        "read_timeout": _positive_int(values.get("BB_REQUEST_READ_TIMEOUT") or os.environ.get("BB_REQUEST_READ_TIMEOUT"), "read timeout", DEFAULT_READ_TIMEOUT_SECONDS),
    }
