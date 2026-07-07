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
- [x] Step 5 — Text injection (src/injector.py) **[Mac-only: keyboard control]** — confirmed working live 2026-07-07 (typed into TextEdit)
- [x] Step 6 — AI cleanup mode (src/cleanup.py) — code done + wired into app.py; fallback-to-raw-text path confirmed (no API key configured yet, so live LLM cleanup itself is untested — see below)
- [x] Step 7 — Menu bar app (rumps) **[Mac-only]** — confirmed working live 2026-07-07
- [x] Step 8 — Custom dictionary & polish — `user_dictionary.json` + `src/dictionary.py` wired in; single error-handling guard added around the whole transcribe→clean→dictionary→inject pipeline (mic-permission, model-load, and API failures all print a message and stay usable instead of crashing); automated test in `tests/test_dictation_pipeline.py` passed
- [ ] Step 9 — README, ship it

## Exact next step

Step 9 (final): flesh out `README.md` (what it does, architecture flow in
text, setup-from-fresh-clone incl. permissions walkthrough, config options
table), optionally a launch-agent plist for auto-start on login, final full
test pass of both modes, final commit + push.

Benchmarks (2026-07-07, this Mac): base model cold load 5.9 s (first run
incl. download), 5 s clip transcribed in 0.6 s warm.

Pending manual check: cleanup mode's actual LLM call is untested end-to-end
— no real `VOICETYPE_API_KEY` is in `.env` yet. Verified fallback instead:
with no key, `clean()` catches the API error and returns the raw transcript
unchanged. To test the real call, put a real OpenAI key in `.env`, set
`VOICETYPE_CLEANUP_ENABLED=true`, run `.venv/bin/python -m src.cleanup`.

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
