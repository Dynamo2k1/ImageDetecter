from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator

class Settings(BaseSettings):
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Forensic Evidence Acquisition System"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # --- Database Settings ---
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "forensic_db"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[str] = None

    @validator("DATABASE_URL", pre=True, always=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"

    # --- Storage Settings ---
    STORAGE_TYPE: str = "local"
    LOCAL_STORAGE_PATH: str = "./evidence_storage"
    MAX_FILE_SIZE: int = 500 * 1024 * 1024

    # --- S3 Settings (Optional) ---
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "forensic-evidence"
    S3_REGION: str = "us-east-1"
    S3_SECURE: bool = True

    # --- Redis / Celery Settings ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    # Set USE_CELERY=false to use FastAPI BackgroundTasks instead of Celery
    # Useful for development without Redis/Celery setup
    USE_CELERY: bool = True

    @validator("CELERY_BROKER_URL", pre=True, always=True)
    def assemble_celery_broker(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str): return v
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/0"

    @validator("CELERY_RESULT_BACKEND", pre=True, always=True)
    def assemble_celery_backend(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str): return v
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/0"

    # --- Social Media Keys ---
    TWITTER_CONSUMER_KEY: Optional[str] = None
    TWITTER_CONSUMER_SECRET: Optional[str] = None
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    INSTAGRAM_APP_ID: Optional[str] = None
    INSTAGRAM_APP_SECRET: Optional[str] = None

    # --- App Configuration ---
    ALLOWED_URL_DOMAINS: List[str] = [
        "twitter.com",
        "x.com",
        "youtube.com",
        "youtu.be",
        "facebook.com",
        "fb.watch",
        "fb.com",
        "instagram.com"
    ]

    ALLOWED_MIME_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/heic",
        "image/heif",
        "video/mp4",
        "video/quicktime",
        "video/x-msvideo",
        "audio/mpeg",
        "audio/wav"
    ]

    # --- Critical Missing Fields Restored ---
    RATE_LIMIT_PER_MINUTE: int = 60
    LOG_LEVEL: str = "INFO"
    CHAIN_OF_CUSTODY_LOG_PATH: str = "./chain_of_custody.log"

    # FEAS 2.0 Configuration
    FEAS_ENCRYPTION_KEY: Optional[str] = None
    NVD_API_KEY: Optional[str] = None
    ALLOW_INTERNAL_SCAN: bool = False
    
    # --- Default Admin Credentials ---
    # SECURITY WARNING: These are development defaults only!
    # In production, set these via environment variables:
    #   DEFAULT_ADMIN_EMAIL=your-secure-email@domain.com
    #   DEFAULT_ADMIN_PASSWORD=<secure-random-password>
    # The admin user is only created if no admin exists in the database.
    DEFAULT_ADMIN_EMAIL: str = "admin@feas.local"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"  # This prevents crashes if .env has extra keys
    }

settings = Settings()