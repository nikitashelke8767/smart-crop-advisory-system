from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Smart Crop Advisory System"
    debug: bool = True
    api_prefix: str = "/api"
    upload_dir: str = "uploads"


settings = Settings()
