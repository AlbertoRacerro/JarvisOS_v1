from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class JarvisPaths:
    data_root: Path
    database_file: Path
    workspaces_dir: Path
    artifacts_dir: Path
    logs_dir: Path

    @property
    def data_root_exists(self) -> bool:
        return self.data_root.exists()

    def as_strings(self) -> dict[str, str]:
        return {
            "data_root": str(self.data_root),
            "database_file": str(self.database_file),
            "workspaces_dir": str(self.workspaces_dir),
            "artifacts_dir": str(self.artifacts_dir),
            "logs_dir": str(self.logs_dir),
        }


def build_paths(settings: Settings | None = None) -> JarvisPaths:
    resolved = settings or get_settings()
    return JarvisPaths(
        data_root=resolved.data_root,
        database_file=resolved.database_path,
        workspaces_dir=resolved.data_root / "workspaces",
        artifacts_dir=resolved.data_root / "artifacts",
        logs_dir=resolved.data_root / "logs",
    )


def ensure_data_directories(paths: JarvisPaths | None = None) -> JarvisPaths:
    resolved = paths or build_paths()
    for directory in [
        resolved.data_root,
        resolved.workspaces_dir,
        resolved.artifacts_dir,
        resolved.logs_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)
    return resolved
