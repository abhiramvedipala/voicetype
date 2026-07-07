"""Confirms a failure anywhere in transcribe/clean/dictionary/inject is
swallowed — the listener must never crash or get stuck on a bad dictation."""

from unittest.mock import patch

from src.app import HotkeyListener
from src.config import settings


def test_pipeline_failure_is_swallowed():
    calls = []
    listener = HotkeyListener(on_transcribed=calls.append)

    with patch("src.app.transcribe", side_effect=RuntimeError("boom")):
        listener._on_press(listener._key)
        listener._press_time -= 1  # pretend enough time passed to not be a tap
        listener._on_release(listener._key)  # must not raise

    assert calls == []  # failed dictation never reaches injection
    assert listener._pressed is False  # ready for the next press


def test_pipeline_happy_path_applies_dictionary():
    calls = []
    listener = HotkeyListener(on_transcribed=calls.append)

    # Isolate from whatever cleanup/prompt mode is set in the local .env —
    # this test only cares about the dictionary step, not the LLM.
    with (
        patch("src.app.transcribe", return_value="open cloud code now"),
        patch.object(settings, "cleanup_enabled", False),
        patch.object(settings, "prompt_mode", False),
    ):
        listener._on_press(listener._key)
        listener._press_time -= 1
        listener._on_release(listener._key)

    assert calls == ["open Claude Code now"]  # dictionary fix reached the callback


if __name__ == "__main__":
    test_pipeline_failure_is_swallowed()
    test_pipeline_happy_path_applies_dictionary()
    print("dictation pipeline tests OK")
