"""Microphone capture: 16 kHz mono push-to-talk recording.

Whisper models are trained on 16 kHz mono audio, so we record in exactly
that format — the transcriber can consume the array as-is, no resampling.
"""

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16_000  # Hz — whisper's expected input


class Recorder:
    """Push-to-talk: start() on key press, stop() on release returns audio."""

    def __init__(self) -> None:
        self._chunks: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None

    def start(self) -> None:
        self._chunks = []
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=lambda indata, frames, time, status: self._chunks.append(
                indata.copy()
            ),
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        """Stop recording and return mono float32 audio in [-1, 1]."""
        assert self._stream is not None, "stop() called before start()"
        self._stream.stop()
        self._stream.close()
        self._stream = None
        if not self._chunks:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(self._chunks)[:, 0]


if __name__ == "__main__":
    # Mic check: python -m src.audio  → records 3 s, saves test_recording.wav
    import time
    import wave

    print("Recording 3 seconds — say something!")
    rec = Recorder()
    rec.start()
    time.sleep(3)
    audio = rec.stop()

    peak = float(np.abs(audio).max()) if audio.size else 0.0
    print(f"Captured {audio.size} samples ({audio.size / SAMPLE_RATE:.1f}s), peak {peak:.3f}")
    if peak < 0.01:
        print("Looks silent — check System Settings → Privacy & Security → Microphone.")

    with wave.open("test_recording.wav", "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)  # 16-bit PCM
        f.setframerate(SAMPLE_RATE)
        f.writeframes((audio * 32767).astype(np.int16).tobytes())
    print("Saved test_recording.wav — play it to verify.")
