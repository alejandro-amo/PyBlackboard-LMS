"""Standard-stream encoding helpers."""

from __future__ import annotations

import sys
from typing import Any


def force_utf8_standard_streams() -> None:
    """Configure reconfigurable standard text streams to use UTF-8."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")
