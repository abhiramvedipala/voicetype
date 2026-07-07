"""Post-transcription word fixes — corrects words Whisper reliably mishears.

A speech-to-text model predicts the most statistically likely word for a
sound, not the word you actually meant. Rare proper nouns, product names,
and jargon ("Claude Code", unusual names) often lose to a common word that
just sounds similar, because the common word is far more frequent in the
model's training data. A small fixed dictionary catches these known misses
cheaply — no bigger/slower model needed, just a lookup table you maintain
yourself as you notice mistakes.

Edit user_dictionary.json at the repo root to add your own entries.
Matching is whole-word/phrase, case-insensitive; the replacement uses
exactly the casing you write in the JSON file.
"""

import json
import re
from pathlib import Path

_DICT_PATH = Path(__file__).resolve().parent.parent / "user_dictionary.json"
_dictionary: dict[str, str] | None = None


def _load() -> dict[str, str]:
    global _dictionary
    if _dictionary is None:
        try:
            _dictionary = json.loads(_DICT_PATH.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            _dictionary = {}
    return _dictionary


def apply_dictionary(text: str) -> str:
    for wrong, right in _load().items():
        text = re.sub(rf"\b{re.escape(wrong)}\b", right, text, flags=re.IGNORECASE)
    return text


if __name__ == "__main__":
    sample = "open cloud code and check the voice type repo"
    print("Before:", sample)
    print("After: ", apply_dictionary(sample))
