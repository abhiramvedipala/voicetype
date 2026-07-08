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

## Post-v1: Part A — Ollama local backend (2026-07-07)

Cleanup mode now works fully offline/free via Ollama, in addition to
Gemini (Step above) and OpenAI. **Zero code changes needed in
`cleanup.py`** — it already only read `api_key` / `llm_model` /
`llm_base_url` generically; Ollama support is entirely a `.env` change
(this is the whole point of the OpenAI-compatible-endpoint pattern, see
README's "Cleanup mode backends" section for the full explanation).

- Installed via `brew install ollama`; `brew services start ollama`
  registers a launchd agent to run it in the background at login.
  **Note:** `brew services start` behaved oddly when run from this agent
  session (job registered but not actually running per `launchctl list`;
  had to fall back to running `ollama serve` directly to test) — likely a
  launchd/session quirk specific to how this sandboxed tool session talks
  to launchd, not expected to reproduce in a normal Terminal. Worth
  double-checking `brew services list` shows `started` after a real login.
- Pulled and live-tested both `llama3.2:3b` and `qwen2.5:3b`. Chose
  **`qwen2.5:3b`** as the default — in side-by-side testing on the same
  messy transcripts, `llama3.2:3b` paraphrased more than instructed
  (changed "i wanted to ask if you could fix" → "I'd like to report a
  bug"; turned a question into a command), while `qwen2.5:3b` preserved
  wording much more literally. Both are the same size class (~2GB,
  ~0.6s/call on this Apple Silicon Mac — no noticeable latency vs.
  transcription itself).
- Tightened `_CLEANUP_PROMPT` twice: first attempt (adding an inline
  "the the bug" → "the bug" example) actually made `llama3.2:3b` rewrite
  *more* aggressively, not less — the example seemed to prime it toward
  general rewriting rather than a narrow fix. Second attempt (numbered
  rules, explicit "do not rephrase, keep every other word in the exact
  order," no inline arrow example) worked better on both models.
- New config fields: none — Ollama reuses `api_key` / `llm_model` /
  `llm_base_url` from the Gemini work. `VOICETYPE_API_KEY=ollama` (or any
  non-empty string) is required even though Ollama doesn't check it — the
  `openai` client library itself needs a non-empty string.

## Post-v1: Part B — daily-driver setup (2026-07-07)

Docs-only step (no app code changed).
- README rewritten: proper macOS permissions walkthrough that explains the
  per-executable TCC gotcha (grant to `.venv/bin/python` for auto-start, not
  just to the terminal), a one-page **Daily usage** section (hotkey, status
  icons, mode toggles, dictionary editing), and a corrected auto-start
  section — the old `sed` used the wrong placeholder (`/path/to/voicetype`
  vs the template's `/ABSOLUTE/PATH/TO/voicetype`) so it silently produced a
  broken plist; fixed.
- Recommended **LaunchAgent** over a Login Item (Login Items need a `.app`
  bundle; we have `python -m src.app`, so a LaunchAgent is the right tool).
- Generated a real, path-filled plist at
  `~/Library/LaunchAgents/com.voicetype.app.plist` (validated with
  `plutil -lint`) but deliberately did NOT `launchctl load` it — loading
  must happen AFTER the user grants Accessibility/Mic to the python binary,
  and can't be verified from this sandboxed session. User runs the two-step
  load themselves (documented in README).
- Note: that generated plist has the CURRENT path baked in
  (`.../voicetype- WF`). It must be regenerated after the folder rename —
  the README's `sed "s|...|$(pwd)|"` recipe handles this.

## Exact next step

Roadmap + both post-v1 parts complete. Remaining optional follow-ups:
- **Grant permissions + load the LaunchAgent** — user action, needs a real
  login session (see README "Auto-start on login").
- Rename the project folder (drop the `- WF` / space), then regenerate the
  LaunchAgent plist — user's follow-up task.
- Persist the menu bar's mic picker choice to `.env` (currently session-only
  by design, see `ponytail:` comment in `src/app.py`).
- Confirm `brew services list` shows ollama `started` from a real Terminal
  (the `brew services` quirk noted in Part A was likely sandbox-specific).

Benchmarks (2026-07-07, this Mac): base model cold load 5.9 s (first run
incl. download), 5 s clip transcribed in 0.6 s warm. Cleanup call via
Ollama (`qwen2.5:3b`, warm): ~0.6s.

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
