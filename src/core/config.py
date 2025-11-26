"""
Configurações da aplicação
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente"""

    # Database
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "blogdb"
    database_user: str = "postgres"
    database_password: str = "postgres"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # App
    app_name: str = "Blog Workshop"
    app_version: str = "1.0.0"
    debug: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância singleton das configurações"""
    return Settings()
