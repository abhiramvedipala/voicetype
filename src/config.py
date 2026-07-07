"""App settings, loaded from .env / environment variables.

Every setting has a safe default, so the app runs with no .env at all.
Set VOICETYPE_* variables in .env to override (see .env.example).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="VOICETYPE_", env_file=".env", extra="ignore"
    )

    hotkey: str = "alt_r"  # right Option key
    whisper_model: str = "base"  # tiny | base | small | medium
    inject_mode: str = "keystrokes"  # keystrokes | clipboard
    cleanup_enabled: bool = False
    prompt_mode: bool = False
    api_key: str = ""
    llm_model: str = "gpt-4o-mini"  # e.g. "gemini-2.0-flash" if using Gemini
    llm_base_url: str = ""  # empty = OpenAI's default; set to point at a compatible API (e.g. Gemini)
    use_api_transcription: bool = False


settings = Settings()
