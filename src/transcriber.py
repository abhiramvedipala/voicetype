"""Speech-to-text: local faster-whisper by default, OpenAI API optional.

The model is loaded once and cached in the module (warm start): first call
pays the load cost, every later dictation reuses it. First run ever also
downloads the model weights to ~/.cache/huggingface/hub.
"""

import numpy as np

from src.config import settings

_model = None  # loaded lazily, then kept warm for the app's lifetime


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        # int8 on CPU: fastest option on Apple Silicon (no GPU support in
        # ctranslate2 for Metal; int8 quantization roughly halves compute)
        _model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")
    return _model


def transcribe(audio: np.ndarray) -> str:
    """16 kHz mono float32 array (from Recorder) -> text."""
    if audio.size == 0:
        return ""
    if settings.use_api_transcription:
        return _transcribe_api(audio)
    segments, _info = _get_model().transcribe(audio)
    return " ".join(seg.text.strip() for seg in segments).strip()


def _transcribe_api(audio: np.ndarray) -> str:
    """OpenAI hosted whisper: faster on weak hardware, costs money,
    and your voice leaves the machine (privacy tradeoff)."""
    import io
    import wave

    from openai import OpenAI

    buf = io.BytesIO()
    with wave.open(buf, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16_000)
        f.writeframes((audio * 32767).astype(np.int16).tobytes())
    buf.seek(0)
    buf.name = "audio.wav"  # the API needs a filename to sniff the format

    client = OpenAI(api_key=settings.api_key)
    result = client.audio.transcriptions.create(model="whisper-1", file=buf)
    return result.text.strip()


if __name__ == "__main__":
    # Benchmark: python -m src.transcriber  → records 5 s, times cold + warm
    import time

    from src.audio import Recorder

    print("Recording 5 seconds — speak!")
    rec = Recorder()
    rec.start()
    time.sleep(5)
    audio = rec.stop()

    t0 = time.perf_counter()
    _get_model()
    print(f"Model load (cold start): {time.perf_counter() - t0:.1f}s")

    t0 = time.perf_counter()
    text = transcribe(audio)
    print(f"Transcribe 5s clip (warm): {time.perf_counter() - t0:.1f}s")
    print(f"Text: {text!r}")
