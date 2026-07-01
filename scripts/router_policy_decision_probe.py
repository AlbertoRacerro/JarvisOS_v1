"""Compatibility re-export for the canonical RouterPolicy decision producer."""

from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.ai.routing import decision as _canonical  # noqa: E402


for name in dir(_canonical):
    if not name.startswith("__"):
        globals()[name] = getattr(_canonical, name)

__all__ = tuple(name for name in dir(_canonical) if not name.startswith("__"))
