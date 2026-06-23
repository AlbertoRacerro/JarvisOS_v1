import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DEFAULT_DATA_ROOT = Path(r"C:\JarvisOS")


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    environment: str
    data_root: Path
    database_filename: str
    ai_provider: str
    cors_origins: list[str]

    @property
    def database_path(self) -> Path:
        return self.data_root / self.database_filename


def _split_origins(value: str) -> list[str]:
    return [origin.strip() for origin in value.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    data_root = Path(os.getenv("JARVISOS_DATA_ROOT", str(DEFAULT_DATA_ROOT)))
    cors_origins = _split_origins(
        os.getenv("JARVISOS_CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173")
    )

    return Settings(
        app_name=os.getenv("JARVISOS_APP_NAME", "JarvisOS"),
        app_version=os.getenv("JARVISOS_APP_VERSION", "0.1.0"),
        environment=os.getenv("JARVISOS_ENV", "local"),
        data_root=data_root,
        database_filename=os.getenv("JARVISOS_DATABASE_FILENAME", "jarvisos.db"),
        ai_provider=os.getenv("JARVISOS_AI_PROVIDER", "none"),
        cors_origins=cors_origins,
    )
