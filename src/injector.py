"""Types transcribed text into whatever app currently has focus.

Two modes (set VOICETYPE_INJECT_MODE):
- "keystrokes" (default): simulate typing each character. Works in any app,
  but visibly slower for long text and some apps (certain editors, games)
  intercept individual keystrokes oddly.
- "clipboard": copy text to the clipboard and simulate Cmd+V. Instant
  regardless of length, but it overwrites whatever you had copied —
  a real tradeoff if you use copy/paste in your normal workflow.
"""

import subprocess

from pynput.keyboard import Controller, Key

from src.config import settings

_keyboard = Controller()


def inject(text: str) -> None:
    if not text:
        return
    if settings.inject_mode == "clipboard":
        _inject_clipboard(text)
    else:
        _keyboard.type(text)


def _inject_clipboard(text: str) -> None:
    subprocess.run(["pbcopy"], input=text.encode(), check=True)
    with _keyboard.pressed(Key.cmd):
        _keyboard.tap("v")


if __name__ == "__main__":
    # Clipboard round-trip check — does NOT send any keystrokes anywhere,
    # so it's safe to run without knowing what window has focus.
    sample = "voicetype clipboard check"
    subprocess.run(["pbcopy"], input=sample.encode(), check=True)
    pasted = subprocess.run(["pbpaste"], capture_output=True, text=True, check=True).stdout
    assert pasted == sample, f"clipboard round-trip failed: {pasted!r}"
    print("pbcopy/pbpaste round-trip OK — clipboard mode's plumbing works.")
    print("Full inject() test (keystrokes + Cmd+V) needs a live run with a")
    print("real focused text field — see PROJECT_LOG.md for the manual test.")
