from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str = "redis://redis:6379"

    keycloak_url: str
    keycloak_realm: str
    keycloak_client_id: str
    keycloak_client_secret: str

    secret_key: str
    environment: str = "development"
    log_level: str = "INFO"

    smtp_host: str = "mailhog"
    smtp_port: int = 1025
    smtp_from: str = "statusforge@localhost"
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = False


settings = Settings()
