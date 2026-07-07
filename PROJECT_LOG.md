# VoiceType — Project Log

Wispr Flow-style push-to-talk dictation for macOS. Hold a hotkey, speak,
release — words get typed into whatever app has focus. Optional AI cleanup.

GitHub is the single source of truth. Read this file + `git log` at the start
of every session.

## Status checklist

- [x] Step 1 — Repo & scaffolding (structure, config.py, pinned deps, first push)
- [x] Step 2 — Audio capture (src/audio.py) **[Mac-only: needs mic]**
- [x] Step 3 — Local transcription (src/transcriber.py) **[Mac-only: model download + benchmark]**
- [ ] Step 4 — Global hotkey (src/app.py) **[Mac-only: Accessibility permission]**
- [ ] Step 5 — Text injection (src/injector.py) **[Mac-only: keyboard control]**
- [ ] Step 6 — AI cleanup mode (src/cleanup.py) — code can be written anywhere, testing needs Mac
- [ ] Step 7 — Menu bar app (rumps) **[Mac-only]**
- [ ] Step 8 — Custom dictionary & polish
- [ ] Step 9 — README, ship it

## Exact next step

Step 4: global hotkey in `src/app.py` — pynput listener, hold right-Option
to record, release to stop+transcribe, taps under 0.3 s cancel. **Mac-only:
needs Accessibility permission for the terminal.**

Benchmarks (2026-07-07, this Mac): base model cold load 5.9 s (first run
incl. download), 5 s clip transcribed in 0.6 s warm. Mic test passed.

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
