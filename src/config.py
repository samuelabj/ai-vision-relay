from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    BLUE_ONYX_URL: str = "http://localhost:5000"
    SPECIESNET_REGION: str = "AUS"
    SPECIESNET_BLANK_LABEL: str = "f1856211-cfb7-4a5b-9158-c0f72fd09ee6;;;;;;blank"
    TRIGGER_LABELS: List[str] = ["animal", "cat", "dog", "bird"]
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
