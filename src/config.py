from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Axpo FAA API"
    aemet_api_key: str
    database_name: str
    model_config = SettingsConfigDict(env_file="../.env")