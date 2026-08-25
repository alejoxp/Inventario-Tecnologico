from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion tipada cargada desde el archivo .env del proyecto."""

    db_user: str = "postgres"
    db_password: str = "postgres"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "inventario_fundacite"
    secret_key: str = "cambiar-en-produccion"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    admin_username: str = "admin"
    admin_password: str = "cambiar-en-produccion"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        """Construye la URL async-free compatible con psycopg2 y SQLAlchemy."""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """Conserva una unica instancia de configuracion durante el proceso."""
    return Settings()


settings = get_settings()
