"""Global hotkey (Step 4) + menu-bar wiring (Step 7 — not yet implemented).

Hold the configured key to record, release to transcribe. Taps shorter than
MIN_HOLD_SECONDS are treated as accidental and cancelled, not transcribed.
"""

import time

from pynput import keyboard

from src.audio import Recorder
from src.config import settings
from src.injector import inject
from src.transcriber import transcribe

MIN_HOLD_SECONDS = 0.3  # taps shorter than this are accidental, not intended


def _type_it(text: str) -> None:
    print(f"-> {text!r}")
    inject(text)


class HotkeyListener:
    """Push-to-talk over a single global key (default: right Option)."""

    def __init__(self, on_transcribed=_type_it) -> None:
        self._key = getattr(keyboard.Key, settings.hotkey)
        self._on_transcribed = on_transcribed
        self._recorder = Recorder()
        self._pressed = False  # guards against macOS's key-repeat on_press spam
        self._press_time = 0.0

    def _on_press(self, key) -> None:
        if key != self._key or self._pressed:
            return
        self._pressed = True
        self._press_time = time.monotonic()
        self._recorder.start()

    def _on_release(self, key) -> None:
        if key != self._key or not self._pressed:
            return
        self._pressed = False
        audio = self._recorder.stop()

        held_for = time.monotonic() - self._press_time
        if held_for < MIN_HOLD_SECONDS:
            return  # accidental tap — discard, don't transcribe

        text = transcribe(audio)
        if text:
            self._on_transcribed(text)

    def run(self) -> None:
        """Blocks forever, listening for the hotkey."""
        with keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release
        ) as listener:
            listener.join()


if __name__ == "__main__":
    print(f"Hold {settings.hotkey} to record, release to transcribe. Ctrl+C to quit.")
    HotkeyListener().run()
