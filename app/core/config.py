from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AliasChoices, Field, model_validator
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

    # Image storage backend: "local" (disk, dev + tests) or "s3" (production).
    # Defaults to "local" so nothing needs AWS to run the suite.
    STORAGE_BACKEND: str = Field(default="local")

    S3_BUCKET: str = Field(default="", description="Bucket name; required when STORAGE_BACKEND=s3")
    S3_REGION: str = Field(default="us-east-1", description="Bucket region")
    S3_PREFIX: str = Field(default="", description="Optional key prefix, e.g. 'prod'")
    S3_PRESIGN_TTL: int = Field(default=3600, description="Presigned URL lifetime (seconds)")
    
    
    @classmethod
    @lru_cache
    def get_instance(cls) -> "Settings":
        return cls()
    
    @property
    def use_s3(self) -> bool:
        """True when images live in S3 instead of local disk."""

        return self.STORAGE_BACKEND.strip().lower() == "s3"

    @model_validator(mode="after")
    def _check_s3_config(self) -> "Settings":
        """Fail at boot, not at first upload, if S3 is selected without a bucket."""

        if self.use_s3 and not self.S3_BUCKET:

            raise ValueError("STORAGE_BACKEND=s3 requires S3_BUCKET to be set.")

        return self

    @property
    def allowed_origins_list(self) -> list[str]:
        """Convierte ALLOW_ORIGIn STRINg TO FastAPI CORS."""
        
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]



@lru_cache
def get_settings() -> Settings:
    
    return Settings()



settings = Settings.get_instance()

