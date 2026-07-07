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
- [x] Step 9 — README, ship it — full README (architecture, setup, permissions, config table, launchd template) written; all modules import cleanly; both test files pass

## Status: v1 shipped (2026-07-07)

All 9 roadmap steps complete. Core loop (hotkey → record → transcribe →
cleanup → dictionary → inject) confirmed working live on this Mac.

## Exact next step

Nothing queued. Natural follow-ups if picked up later:
- Rename the project folder (drop the `- WF` / space) — user's follow-up
  task, not done by an agent session.
- Persist the menu bar's mic picker choice to `.env` (currently session-only
  by design, see `ponytail:` comment in `src/app.py`).
- Cleanup prompt could be tightened — one live test left a duplicated word
  ("the the bug") uncorrected; not a wiring bug, just prompt quality.

Cleanup mode confirmed working live end-to-end 2026-07-07 using Gemini via
its OpenAI-compatible endpoint (`VOICETYPE_LLM_BASE_URL` +
`VOICETYPE_LLM_MODEL`, both new config fields, see Key decisions below).
`gemini-2.0-flash` had 0 free-tier quota on the tested account;
`gemini-2.5-flash` worked. `.env` (local, gitignored) holds the real key —
never commit it.

Benchmarks (2026-07-07, this Mac): base model cold load 5.9 s (first run
incl. download), 5 s clip transcribed in 0.6 s warm.

## Key decisions

- **Local-first transcription** (faster-whisper) — free, offline, private.
  Config flag will allow OpenAI whisper API later (Step 3).
- **Cleanup mode's LLM provider is configurable, not hardcoded to OpenAI**
  — `VOICETYPE_LLM_BASE_URL` + `VOICETYPE_LLM_MODEL` let you point the same
  `openai` SDK client at any OpenAI-compatible endpoint (Gemini included),
  no new dependency needed.
- **Tests must isolate from local `.env`** — `test_pipeline_happy_path_...`
  broke when `.env` had cleanup mode on for manual testing, because it
  shares the same `settings` singleton as the real app. Fixed by patching
  `settings.cleanup_enabled` / `settings.prompt_mode` to `False` inside the
  test itself rather than relying on ambient defaults.
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
