from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    secretkey: Optional[str] = None
    algorithm: str = "placeholder"
    expire_min: int = 3
    db_password: Optional[str] = None
    db_name: Optional[str] = None
    db_port: Optional[int] = None
    db_hostname: Optional[str] = None
    db_username: Optional[str] = None

settings = Settings()

