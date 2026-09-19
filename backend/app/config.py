from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Settings
    LLM_PROVIDER: str = "gemini"
    LLM_MODEL_VISION: str = "gemini-2.5-flash"
    LLM_MODEL_TEXT: str = "gemini-2.5-flash"
    LLM_API_KEY: Optional[str] = None

    # Operational settings
    DEMO_MODE: bool = False
    TIMEOUT_SECONDS: float = 30.0
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_ORIGINS: str = "*"

    @property
    def cors_origins(self) -> List[str]:
        if not self.ALLOWED_ORIGINS or self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def is_demo_mode(self) -> bool:
        # If explicitly enabled or no API key is provided, enable DEMO_MODE for fail-safe operation
        return self.DEMO_MODE or not self.LLM_API_KEY


settings = Settings()
