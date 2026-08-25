from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'OAN Catalog Registry API'
    database_url: str = 'postgresql+psycopg2://oan:oan@postgres:5432/oan_catalog'
    redis_url: str = 'redis://redis:6379/0'

    keycloak_base_url: str = 'http://keycloak:8080'
    keycloak_realm: str = 'oan'
    keycloak_client_id: str = 'oan-portal'
    keycloak_client_secret: str = 'oan-portal-secret'

    auth_enabled: bool = True


settings = Settings()
