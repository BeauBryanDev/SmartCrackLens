from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(Path(__file__).parent.parent / ".env")


class Settings(BaseSettings):
    """
    App settings from environment and optional `.env`.

    `extra="ignore"` allows keys like ``MONGO_USER`` / ``MONGO_PASSWORD`` used only
    by docker-compose interpolation without breaking validation.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    MONGO_URI: str = Field(..., description="MongoDB URI")
    DB_NAME: str = Field(..., description="Database name")
    MODEL_PATH: str = Field(..., description="Model path")
    CONFIDENCE_THRESHOLD: float = Field(..., description="Confidence threshold")
    ALLOWED_ORIGINS: str = Field(..., description="Allowed origins")

    JWT_SECRET_KEY: str = Field(
        ...,
        validation_alias=AliasChoices("JWT_SECRET_KEY", "JWT_SECRET"),
        description="JWT signing secret",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRE_MINUTES: int = Field(default=60, description="JWT access token TTL (minutes)")

    APP_NAME: str = Field(default="SmartCrackLens")
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)
    
    
    @classmethod
    @lru_cache
    def get_instance(cls) -> "Settings":
        return cls()
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """Convierte ALLOW_ORIGIn STRINg TO FastAPI CORS."""
        
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]



@lru_cache
def get_settings() -> Settings:
    
    return Settings()



settings = Settings.get_instance()

