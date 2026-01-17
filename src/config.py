from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    BLUE_ONYX_URL: str = "http://localhost:5000"
    SPECIESNET_REGION: str = "AUS"
    TRIGGER_LABELS: List[str] = ["animal", "cat", "dog", "bird"]
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    class Config:
        env_file = ".env"

settings = Settings()
