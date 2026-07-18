"""
Centralized application configuration.

All environment-dependent values live here and NOWHERE else. Every other
module imports `settings` from this file instead of calling os.getenv
directly. This keeps configuration auditable and testable (settings can be
overridden in tests via env vars or a `.env.test` file).

Note on list-typed settings (BACKEND_CORS_ORIGINS, IMAGE_PROVIDER_ORDER,
TTS_PROVIDER_ORDER): pydantic-settings attempts to JSON-decode ANY
List/Dict/Set-typed field read from an environment variable *before* any
field_validator runs. A plain comma-separated string like
"http://localhost:5173" is not valid JSON, so without opting out of that
behavior via `NoDecode`, startup fails with a SettingsError. Each affected
field below is annotated with `NoDecode` for exactly this reason — do not
remove it without also removing the corresponding "before" validator, or
plain comma-separated .env values will break again.
"""
from functools import lru_cache
from typing import Annotated, List, Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "Lumora"
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # --- Security / Auth ---
    SECRET_KEY: str = Field(..., description="Used to sign JWTs. MUST be set in production.")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 14  # 14 days
    JWT_ALGORITHM: str = "HS256"

    # --- CORS ---
    BACKEND_CORS_ORIGINS: Annotated[List[str], NoDecode] = ["http://localhost:5173"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # --- Database ---
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://lumora:lumora@localhost:5432/lumora",
        description="SQLAlchemy async/sync connection string",
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_ALWAYS_EAGER: bool = False  # set True in tests to run tasks synchronously

    # --- LLM Providers (OpenRouter primary) ---
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: AnyHttpUrl = "https://openrouter.ai/api/v1"
    OPENROUTER_RESEARCH_MODEL: str = "perplexity/sonar"
    OPENROUTER_SCRIPT_MODEL: str = "anthropic/claude-3.5-sonnet"
    OPENROUTER_SCENE_MODEL: str = "anthropic/claude-3.5-sonnet"
    OPENROUTER_SEO_MODEL: str = "openai/gpt-4o-mini"
    LLM_REQUEST_TIMEOUT_SECONDS: int = 90
    LLM_MAX_RETRIES: int = 2

    # --- Image generation providers (ordered fallback chain) ---
    STABILITY_API_KEY: str = ""
    REPLICATE_API_TOKEN: str = ""
    OPENAI_API_KEY: str = ""  # used for DALL-E fallback
    IMAGE_PROVIDER_ORDER: Annotated[List[str], NoDecode] = ["stability", "replicate", "openai"]

    @field_validator("IMAGE_PROVIDER_ORDER", mode="before")
    @classmethod
    def split_providers(cls, v):
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v

    # --- TTS providers ---
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_DEFAULT_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"
    TTS_PROVIDER_ORDER: Annotated[List[str], NoDecode] = ["elevenlabs", "gtts"]

    @field_validator("TTS_PROVIDER_ORDER", mode="before")
    @classmethod
    def split_tts(cls, v):
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v

    # --- Storage ---
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    LOCAL_STORAGE_ROOT: str = "./storage"
    PUBLIC_ASSET_BASE_URL: str = "http://localhost:8000/static"
    S3_BUCKET: str = ""
    S3_REGION: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    STORAGE_MAX_AGE_SECONDS: int = 60 * 60 * 24

    # --- Demo mode ---
    DEMO_MODE: bool = False
    DEMO_MAX_VIDEO_DURATION_SECONDS: int = 20
    DEMO_MAX_SCENES: int = 4
    DEMO_VIDEO_RESOLUTION: str = "720x1280"
    DEMO_VIDEO_FPS: int = 15
    DEMO_TTS_PROVIDER_ORDER: Annotated[List[str], NoDecode] = ["gtts", "elevenlabs"]
    DEMO_IMAGE_PROVIDER_ORDER: Annotated[List[str], NoDecode] = ["stability", "replicate"]

    @field_validator("DEMO_TTS_PROVIDER_ORDER", mode="before")
    @classmethod
    def split_demo_tts_providers(cls, v):
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v

    @field_validator("DEMO_IMAGE_PROVIDER_ORDER", mode="before")
    @classmethod
    def split_demo_image_providers(cls, v):
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v

    # --- FFmpeg ---
    FFMPEG_BINARY: str = "ffmpeg"
    FFPROBE_BINARY: str = "ffprobe"
    VIDEO_DEFAULT_RESOLUTION: str = "1080x1920"  # portrait short-form default
    VIDEO_DEFAULT_FPS: int = 30

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 60

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — avoids re-parsing env on every import."""
    return Settings()


settings = get_settings()
