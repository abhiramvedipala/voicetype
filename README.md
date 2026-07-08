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
 
## Setup & Usage

### 1. Installation

```bash
git clone https://github.com/abhiramvedipala/voicetype.git
cd voicetype
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # edit hotkey/model/etc. if you want non-default values
```

### 2. macOS permissions (one-time)

VoiceType needs two permissions. **Both attach to the specific program that
runs the app, not to "VoiceType" as a concept** — this matters below.

1. **Microphone** — to record your voice.
2. **Accessibility** — to (a) see the global hotkey system-wide and (b)
   type text into other apps. Without it the hotkey silently does nothing.

**The catch:** macOS grants these per-executable. When you launch by hand
from a terminal, the permission is attributed to *your terminal app*
(Terminal, iTerm2, PyCharm…). When launchd auto-starts it at login, there's
no terminal parent — the permission is attributed to *the Python binary
itself* (`.venv/bin/python`). Those are two different identities, so a grant
to one does **not** carry over to the other.

**Easiest path that covers both:** grant the permissions directly to the
Python binary, which is what auto-start uses anyway.

1. Run it once by hand: `.venv/bin/python -m src.app`
2. Hold the hotkey and speak. macOS will prompt for the mic (click Allow)
   and, for Accessibility, will usually add an entry (often shown as
   "Python" or the binary path) to
   `System Settings → Privacy & Security → Accessibility` — **toggle it on.**
   If nothing appears, click `+`, press `Cmd+Shift+G`, paste the absolute
   path to `.venv/bin/python` (run `pwd` in the repo to get the prefix), and
   add it.
3. Quit and relaunch once so it picks up the new grants.

If the hotkey types nothing, it's almost always Accessibility not being
enabled for the right binary — that's the #1 gotcha.

### 3. Running the app

```bash
.venv/bin/python -m src.app
```

A 🎙 icon appears in your menu bar. That's it — see **Daily usage** below.

## Daily usage

Everything you need day-to-day, one page.

**Dictate anywhere.** Put your cursor wherever you want text — a chat box,
an editor, Notes, a terminal. Hold **right Option (⌥)**, speak, release. The
words type themselves into whatever's focused. (Change the key with
`VOICETYPE_HOTKEY` in `.env`.) Taps shorter than 0.3s are ignored, so a
stray brush of the key won't fire.

**Menu-bar icon = live status:**

| Icon | Meaning |
|---|---|
| 🎙 | Idle — ready, listening for the hotkey |
| 🔴 | Recording — the key is held, capturing your voice |
| ⏳ | Transcribing / cleaning up — release happened, text is on its way |

If it sticks on 🎙 when you hold the key, Accessibility isn't enabled for
the running binary (see permissions above).

**Toggle modes from the menu** (click the 🎙 icon):

- **Cleanup mode** — strips "um/uh/like", fixes punctuation. Needs a cleanup
  backend configured (Ollama = free/local, see below).
- **Prompt mode** — rewrites rambling speech into one clean instruction,
  handy for dictating to Claude Code.
- **Choose mic** — pick a different input device (resets each launch).

A checkmark shows which modes are on. These override the `.env` defaults for
the current session.

**When it mishears a technical term**, teach it — edit
[`user_dictionary.json`](user_dictionary.json) at the repo root:

```json
{
  "cloud code": "Claude Code",
  "voice type": "VoiceType",
  "pie torch": "PyTorch"
}
```

Left side = what Whisper hears (lowercase), right side = what gets typed.
Whole-word, case-insensitive; the fix applies on your *next* dictation, no
restart needed. Speech models guess the statistically likeliest word, so
rare names and jargon lose to common lookalikes — this table is the fix.

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

## Auto-start on login

Recommended approach: a **LaunchAgent** (a per-user launchd job), using the
template in [`launchd/`](launchd/com.voicetype.app.plist.example).

**Why a LaunchAgent and not a "Login Item"?** macOS Login Items
(`System Settings → General → Login Items`) expect a `.app` bundle. VoiceType
isn't a bundle — it's `python -m src.app`. Wrapping it into a `.app` just to
appear there (via py2app/Automator) is extra machinery for no benefit. A
LaunchAgent is purpose-built for "run this command at login," which is
exactly what we have.

**Do permissions first.** Because the LaunchAgent runs `.venv/bin/python`
directly, that binary is the one that needs Microphone + Accessibility (see
[permissions](#2-macos-permissions-one-time) above). Grant them by running
the app manually once *before* installing the agent, or the auto-started
copy will launch but the hotkey won't work.

Then, from the repo root:

```bash
# 1. Generate the plist with your real paths baked in (rename-safe: this
#    reads the CURRENT directory, so re-run it if you ever move the repo).
sed "s|/ABSOLUTE/PATH/TO/voicetype|$(pwd)|g" \
    launchd/com.voicetype.app.plist.example \
    > ~/Library/LaunchAgents/com.voicetype.app.plist

# 2. Load it (also starts it now, thanks to RunAtLoad).
launchctl load ~/Library/LaunchAgents/com.voicetype.app.plist
```

VoiceType now starts at every login. **Quitting from the menu really quits**
(the agent uses `KeepAlive=false` on purpose — with it true, launchd would
relaunch instantly and you could never quit); it comes back at next login.

To stop auto-starting:
```bash
launchctl unload ~/Library/LaunchAgents/com.voicetype.app.plist
rm ~/Library/LaunchAgents/com.voicetype.app.plist
```

Logs (handy if it silently doesn't start): `/tmp/voicetype.log` and
`/tmp/voicetype.err`.

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
