"""Configuration settings for the backend."""
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenRouter LLM Configuration
    openrouter_api_key: str = ""
    llm_model: str = "openai/gpt-5-nano"  # Default model (per hackathon plan)
    llm_base_url: str = "https://openrouter.ai/api/v1"
    
    # ScanSan API
    scansan_api_key: str = ""
    scansan_base_url: str = "https://api.scansan.com"
    use_scansan: bool = False
    
    # Model configuration (PLACEHOLDER - teammate will change these)
    model_provider: str = "stub"  # stub | local_pickle | http
    model_path: str = "./models/model.pkl"
    model_http_url: str = "http://localhost:8000/predict"
    
    # Cache settings
    cache_ttl_seconds: int = 3600
    enable_cache: bool = True
    
    class Config:
        # Support both:
        # - backend/.env (when running from backend/)
        # - repo-root .env (common in this project)
        _here = Path(__file__).resolve()
        env_file = [
            str(_here.parents[1] / ".env"),  # backend/.env
            str(_here.parents[2] / ".env"),  # repo-root/.env
        ]
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
