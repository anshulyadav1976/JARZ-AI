"""Configuration settings for the backend."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ScanSan API
    scansan_api_key: str = ""
    scansan_base_url: str = "https://api.scansan.com/v1"
    use_scansan: bool = False
    
    # Model configuration
    model_provider: str = "stub"  # stub | local_pickle | http
    model_path: str = "./models/model.pkl"
    model_http_url: str = "http://localhost:8001/predict"
    
    # Cache settings
    cache_ttl_seconds: int = 3600
    enable_cache: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
