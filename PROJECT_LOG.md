# VoiceType — Project Log

Wispr Flow-style push-to-talk dictation for macOS. Hold a hotkey, speak,
release — words get typed into whatever app has focus. Optional AI cleanup.

GitHub is the single source of truth. Read this file + `git log` at the start
of every session.

## Status checklist

- [x] Step 1 — Repo & scaffolding (structure, config.py, pinned deps, first push)
- [x] Step 2 — Audio capture (src/audio.py) **[Mac-only: needs mic]**
- [x] Step 3 — Local transcription (src/transcriber.py) **[Mac-only: model download + benchmark]**
- [x] Step 4 — Global hotkey (src/app.py) **[Mac-only: Accessibility permission]** — confirmed working live 2026-07-07
- [x] Step 5 — Text injection (src/injector.py) **[Mac-only: keyboard control]** — code done + wired into app.py; live end-to-end typing test pending (see below)
- [ ] Step 6 — AI cleanup mode (src/cleanup.py) — code can be written anywhere, testing needs Mac
- [ ] Step 7 — Menu bar app (rumps) **[Mac-only]**
- [ ] Step 8 — Custom dictionary & polish
- [ ] Step 9 — README, ship it

## Exact next step

Step 6: AI cleanup mode in `src/cleanup.py` — optional LLM pass that strips
filler words / fixes punctuation (strict prompt, never responds to
content), plus a second "prompt mode" for dictating instructions to Claude
Code. Temperature 0, fallback to raw transcript on API error.

Benchmarks (2026-07-07, this Mac): base model cold load 5.9 s (first run
incl. download), 5 s clip transcribed in 0.6 s warm.

Pending manual check: run `.venv/bin/python -m src.app`, click into
TextEdit, hold right-Option, say "hello world," release — confirm it
actually types into TextEdit (this needs a human at the keyboard, not
scriptable from an agent session).

## Key decisions

- **Local-first transcription** (faster-whisper) — free, offline, private.
  Config flag will allow OpenAI whisper API later (Step 3).
- **pydantic-settings for config** — all knobs come from `.env` via
  `VOICETYPE_*` env vars with safe defaults; no secrets or magic values in code.
- **Pinned requirements.txt** — reproducible installs across sessions.
- **Commit style** — local commits only, author Abhiram Reddy Vedipala,
  push straight to `main`, no bot attribution.

## Mac-only vs anywhere

- Anywhere (incl. iPhone): read/review code, edit PROJECT_LOG, plan, write
  pure logic (cleanup prompts, dictionary format).
- Mac only: anything touching mic, keyboard, permissions, menu bar, or
  running/benchmarking the app.
