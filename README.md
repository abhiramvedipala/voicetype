# VoiceType

Personal push-to-talk voice dictation for macOS, Wispr Flow style: hold a
hotkey anywhere, speak, release — your words get typed into whatever app
has focus. Transcription runs locally and offline via
[faster-whisper](https://github.com/SYSTRAN/faster-whisper); an optional
mode cleans up filler words or reformats rambling speech into a clear
instruction before it's typed.

*(demo GIF goes here)*

## How it works

```
Hold hotkey
   │
   ▼
Recorder (sounddevice)   — captures mic @ 16kHz mono while the key is held
   │  release key → numpy array
   ▼
Transcriber (faster-whisper)  — numpy array → raw text, model kept warm in memory
   │
   ▼
Cleanup (optional)   — LLM strips filler words, or rewrites as one clear
   │                    instruction ("prompt mode", for dictating to Claude Code)
   ▼
Dictionary   — fixes words Whisper reliably mishears (your own terms/names)
   │
   ▼
Injector (pynput)   — types the final text into whatever app has focus
```

Every stage past Recorder degrades gracefully: if transcription fails, the
mic permission is missing, or the cleanup API is down, the app logs it and
stays usable for your next dictation instead of crashing.

## Setup from a fresh clone

```bash
git clone https://github.com/abhiramvedipala/voicetype.git
cd voicetype
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # edit hotkey/model/etc. if you want non-default values
```

### macOS permissions (both required, one-time)

1. **Microphone** — the first time you record, macOS prompts your terminal
   app for mic access. Click Allow. If you miss it or deny it: System
   Settings → Privacy & Security → Microphone → enable your terminal app.
2. **Accessibility** — required for the global hotkey listener to see key
   presses system-wide. macOS won't always prompt for this one
   automatically: go to System Settings → Privacy & Security →
   Accessibility → enable your terminal app yourself.

### Run it

```bash
.venv/bin/python -m src.app
```

Look for the 🎙 icon in your menu bar. Hold the hotkey (default: right
Option), speak, release — the icon cycles 🎙 → 🔴 (recording) → ⏳
(transcribing) → 🎙, and the text types into whatever's focused. Click the
menu bar icon to toggle Cleanup mode, Prompt mode, or pick a different mic.

### Run the tests

No test framework needed — each test file is a runnable script:

```bash
.venv/bin/python -m tests.test_config
.venv/bin/python -m tests.test_dictation_pipeline
```

## Configuration

All settings live in `.env` (copy from `.env.example`), prefixed
`VOICETYPE_`. Every setting has a safe default, so the app runs with no
`.env` at all.

| Variable | Default | Description |
|---|---|---|
| `VOICETYPE_HOTKEY` | `alt_r` | pynput key name for push-to-talk (right Option by default) |
| `VOICETYPE_WHISPER_MODEL` | `base` | faster-whisper model size: `tiny` \| `base` \| `small` \| `medium` — bigger = more accurate, slower |
| `VOICETYPE_INJECT_MODE` | `keystrokes` | `keystrokes` (simulated typing, works everywhere) or `clipboard` (instant paste, overwrites your clipboard) |
| `VOICETYPE_CLEANUP_ENABLED` | `false` | send transcript to an LLM to strip filler words and fix punctuation |
| `VOICETYPE_PROMPT_MODE` | `false` | send transcript to an LLM to rewrite rambling speech as one clear instruction (for dictating to Claude Code) |
| `VOICETYPE_API_KEY` | *(empty)* | API key for whichever cleanup backend you pick below |
| `VOICETYPE_LLM_MODEL` | `gpt-4o-mini` | chat model name, must match the backend |
| `VOICETYPE_LLM_BASE_URL` | *(empty)* | empty = OpenAI; set to any OpenAI-compatible endpoint to swap backends |
| `VOICETYPE_USE_API_TRANSCRIPTION` | `false` | use OpenAI's hosted Whisper API instead of local transcription — faster on weak hardware, costs money, sends audio off-device |

Word replacements for terms Whisper reliably mishears (product names, your
own name) live in `user_dictionary.json` at the repo root — edit it
directly, no restart required beyond the next dictation.

### Cleanup mode backends

`cleanup.py` talks to whatever `VOICETYPE_LLM_BASE_URL` points at using the
`openai` Python SDK — no backend-specific code exists anywhere in this repo.
This works because every backend below implements the same
**OpenAI-compatible chat completions API**: same request shape, same
response shape, different server. Swapping backends is purely a `.env`
edit, three variables together as a matched trio (`API_KEY` + `LLM_MODEL` +
`LLM_BASE_URL`) — the app code never needs to know which one you're using.

| Backend | `VOICETYPE_LLM_BASE_URL` | `VOICETYPE_LLM_MODEL` (tested) | Notes |
|---|---|---|---|
| OpenAI | *(leave empty)* | `gpt-4o-mini` | Original default. Costs money per request. |
| Gemini | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.5-flash` | Free tier available; `gemini-2.0-flash` had **zero** free-tier quota on the tested account — check [aistudio.google.com/apikey](https://aistudio.google.com/apikey) if a model 429s. |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.1-8b-instant` | Fast hosted inference, generous free tier. Not live-tested in this repo — verify before relying on it. |
| Ollama | `http://localhost:11434/v1` | `qwen2.5:3b` | **Fully local, free, no quota, no internet needed.** Requires `ollama serve` running (see below). `VOICETYPE_API_KEY` can be any non-empty string, e.g. `ollama` — Ollama doesn't check it, but the client library requires *something*. |

#### Running cleanup mode fully local with Ollama

No more API quotas, no more cost, your dictation never leaves your Mac.

```bash
brew install ollama
brew services start ollama       # runs in the background, restarts on login
ollama pull qwen2.5:3b           # ~1.9GB download, one-time
```

Then set in `.env`:
```
VOICETYPE_CLEANUP_ENABLED=true
VOICETYPE_API_KEY=ollama
VOICETYPE_LLM_MODEL=qwen2.5:3b
VOICETYPE_LLM_BASE_URL=http://localhost:11434/v1
```

**Why `qwen2.5:3b` over `llama3.2:3b`:** both were tested live against the
same messy transcripts. `llama3.2:3b` sounded more natural but drifted —
it paraphrased "i wanted to ask if you could fix" into "I'd like to report
a bug," and turned a question ("can you open...") into a command ("Open
...”). For a cleanup task that must preserve your exact meaning,
`qwen2.5:3b` followed the "don't rephrase" instruction more literally and
was the better fit, even though it's the same size class. Bigger local
models (7B+) would likely follow instructions even more precisely, at the
cost of slower inference and more RAM — 3B was chosen as the smallest size
that stayed both fast (~0.6s per cleanup call on Apple Silicon, no
noticeable added latency over transcription itself) and reliable enough
for this specific narrow task.

## Auto-start on login (optional)

A launchd template lives at
[`launchd/com.voicetype.app.plist.example`](launchd/com.voicetype.app.plist.example).
To use it: replace the placeholder paths with your actual repo path (run
`pwd` inside the repo), rename the file to drop `.example`, then:

```bash
cp launchd/com.voicetype.app.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.voicetype.app.plist
```

To stop it from auto-starting: `launchctl unload ~/Library/LaunchAgents/com.voicetype.app.plist`.

## Project structure

```
src/
  audio.py        — mic capture (16kHz mono, push-to-talk)
  transcriber.py   — faster-whisper (local) or OpenAI API (optional)
  cleanup.py       — optional LLM filler-word removal / prompt reformatting
  dictionary.py    — post-transcription word fixes
  injector.py      — types the result into the focused app
  app.py           — global hotkey listener + rumps menu-bar shell
  config.py        — settings, loaded from .env
tests/             — runnable scripts, no framework
user_dictionary.json — your custom word replacements
```

See [PROJECT_LOG.md](PROJECT_LOG.md) for build history and design decisions.
