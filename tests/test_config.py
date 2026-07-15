"""Smallest check that settings load with sane defaults."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Settings


def test_defaults():
    s = Settings(_env_file=None)  # ignore any local .env
    assert s.hotkey == "alt_r"
    assert s.whisper_model == "base"
    assert s.cleanup_enabled is False
    assert s.api_key == ""


if __name__ == "__main__":
    test_defaults()
    print("config defaults OK")
