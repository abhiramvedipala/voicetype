"""Global hotkey (Step 4) + menu-bar app (Step 7).

Hold the configured key to record, release to transcribe. Taps shorter than
MIN_HOLD_SECONDS are treated as accidental and cancelled, not transcribed.
"""

import threading
import time

import rumps
from pynput import keyboard

from src.audio import Recorder
from src.cleanup import clean
from src.config import settings
from src.injector import inject
from src.transcriber import transcribe

MIN_HOLD_SECONDS = 0.3  # taps shorter than this are accidental, not intended

ICON_IDLE = "🎙"
ICON_RECORDING = "🔴"
ICON_TRANSCRIBING = "⏳"


def _type_it(text: str) -> None:
    print(f"-> {text!r}")
    inject(text)


class HotkeyListener:
    """Push-to-talk over a single global key (default: right Option)."""

    def __init__(self, on_transcribed=_type_it, on_status=lambda status: None) -> None:
        self._key = getattr(keyboard.Key, settings.hotkey)
        self._on_transcribed = on_transcribed
        self._on_status = on_status
        self._recorder = Recorder()
        self._pressed = False  # guards against macOS's key-repeat on_press spam
        self._press_time = 0.0

    def _on_press(self, key) -> None:
        if key != self._key or self._pressed:
            return
        self._pressed = True
        self._press_time = time.monotonic()
        self._recorder.start()
        self._on_status("recording")

    def _on_release(self, key) -> None:
        if key != self._key or not self._pressed:
            return
        self._pressed = False
        audio = self._recorder.stop()

        held_for = time.monotonic() - self._press_time
        if held_for < MIN_HOLD_SECONDS:
            self._on_status("idle")
            return  # accidental tap — discard, don't transcribe

        self._on_status("transcribing")
        text = transcribe(audio)
        text = clean(text)  # no-op unless cleanup/prompt mode is enabled
        self._on_status("idle")
        if text:
            self._on_transcribed(text)

    def run(self) -> None:
        """Blocks forever, listening for the hotkey."""
        with keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release
        ) as listener:
            listener.join()


class VoiceTypeApp(rumps.App):
    """Menu-bar shell: status icon + toggles, hotkey does the real work."""

    _STATUS_ICON = {
        "idle": ICON_IDLE,
        "recording": ICON_RECORDING,
        "transcribing": ICON_TRANSCRIBING,
    }

    def __init__(self) -> None:
        super().__init__("VoiceType", title=ICON_IDLE, quit_button="Quit")

        self.cleanup_item = rumps.MenuItem("Cleanup mode", callback=self._toggle_cleanup)
        self.cleanup_item.state = settings.cleanup_enabled
        self.prompt_item = rumps.MenuItem("Prompt mode", callback=self._toggle_prompt)
        self.prompt_item.state = settings.prompt_mode
        self.mic_menu = rumps.MenuItem("Choose mic")
        self._build_mic_menu()

        self.menu = [self.cleanup_item, self.prompt_item, self.mic_menu]

        listener = HotkeyListener(on_status=self._set_status)
        threading.Thread(target=listener.run, daemon=True).start()

    def _set_status(self, status: str) -> None:
        # Called from the pynput listener thread; rumps title assignment
        # is safe to call off the main thread for plain text updates.
        self.title = self._STATUS_ICON[status]

    def _toggle_cleanup(self, sender: rumps.MenuItem) -> None:
        settings.cleanup_enabled = not settings.cleanup_enabled
        sender.state = settings.cleanup_enabled

    def _toggle_prompt(self, sender: rumps.MenuItem) -> None:
        settings.prompt_mode = not settings.prompt_mode
        sender.state = settings.prompt_mode

    def _build_mic_menu(self) -> None:
        import sounddevice as sd

        for idx, device in enumerate(sd.query_devices()):
            if device["max_input_channels"] > 0:
                self.mic_menu.add(rumps.MenuItem(device["name"], callback=self._pick_mic(idx)))

    @staticmethod
    def _pick_mic(idx: int):
        def _set(sender: rumps.MenuItem) -> None:
            import sounddevice as sd

            # ponytail: session-only, resets on restart. Persisting the
            # choice to .env is Step 8 polish, not needed for daily use.
            sd.default.device = (idx, None)

        return _set


if __name__ == "__main__":
    VoiceTypeApp().run()
