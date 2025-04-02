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

    inner_port: int
    outer_port: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


config = Settings()  # type: ignore
