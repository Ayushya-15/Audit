"""RiskShield configuration module."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "RiskShield"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./riskshield.db")
    API_KEY: str = os.getenv("API_KEY", "riskshield-dev-key-change-in-prod")
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    ML_MODEL_DIR: str = os.getenv("ML_MODEL_DIR", "ml_models")
    SCAN_INTERVAL_SECONDS: int = 300
    NETWORK_SUBNET: str = os.getenv("NETWORK_SUBNET", "192.168.1.0/24")

    class Config:
        env_file = ".env"


settings = Settings()
