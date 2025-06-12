import os

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(PROJECT_ROOT, ".env")
print(env_file)


class Settings(BaseSettings):
    bot_token: str
    admin_ids: list[int]
    webhook_url: str

    db_host: str
    db_port: int
    db_name: str
    db_pass: str
    db_user: str

    inner_port: int
    outer_port: int

    rus_proxy: str | None = None

    model_config = SettingsConfigDict(env_file=env_file, env_file_encoding="utf-8", extra="ignore")


config = Settings()  # type: ignore
