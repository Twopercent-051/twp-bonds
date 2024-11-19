from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    admin_ids: list[int]
    webhook_url: str

    db_host: str
    db_port: int
    db_name: str
    db_pass: str
    db_user: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


config = Settings()
