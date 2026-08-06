import re
from collections.abc import Collection, Iterable
from pathlib import Path, PurePosixPath

from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse, Response
from starlette.routing import BaseRoute
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

_QVALUE = re.compile(r"^(?:0(?:\.\d{0,3})?|1(?:\.0{0,3})?)$")
_STATIC_ASSET_ROOTS = frozenset({"assets"})


def derive_reserved_roots(routes: Iterable[BaseRoute]) -> frozenset[str]:
    """Derive literal top-level HTTP route roots before the frontend mount."""
    roots: set[str] = set()
    for route in routes:
        if not getattr(route, "methods", None):
            continue
        path = getattr(route, "path", None)
        if not isinstance(path, str) or not path.startswith("/"):
            continue
        first = next((segment for segment in path.split("/") if segment), "")
        if not first or "{" in first or "}" in first:
            continue
        roots.add(first)
    return frozenset(roots)


def _split_quoted(value: str, delimiter: str) -> list[str] | None:
    parts: list[str] = []
    start = 0
    quoted = False
    escaped = False
    for index, character in enumerate(value):
        if escaped:
            escaped = False
            continue
        if quoted and character == "\\":
            escaped = True
            continue
        if character == '"':
            quoted = not quoted
            continue
        if character == delimiter and not quoted:
            parts.append(value[start:index])
            start = index + 1
    if quoted or escaped:
        return None
    parts.append(value[start:])
    return parts


def _accepts_html(scope: Scope) -> bool:
    accept = Headers(scope=scope).get("accept", "")
    items = _split_quoted(accept, ",")
    if items is None:
        return False
    for item in items:
        parts = _split_quoted(item, ";")
        if not parts:
            return False
        media_type, *parameters = (part.strip() for part in parts)
        if media_type.lower() != "text/html":
            continue
        quality = 1.0
        quality_seen = False
        for parameter in parameters:
            name, separator, value = parameter.partition("=")
            if name.strip().lower() != "q":
                continue
            if not separator or quality_seen:
                quality = 0.0
                break
            quality_seen = True
            raw_quality = value.strip()
            if _QVALUE.fullmatch(raw_quality) is None:
                quality = 0.0
                break
            quality = float(raw_quality)
        if quality > 0:
            return True
    return False


def _safe_extensionless_path(path: str) -> bool:
    if "\\" in path or any(ord(character) < 32 for character in path):
        return False
    parts = PurePosixPath(path).parts
    if any(part in {".", ".."} for part in parts):
        return False
    final_segment = PurePosixPath(path).name
    return bool(final_segment) and not Path(final_segment).suffix


class SpaStaticFiles(StaticFiles):
    """Serve a built SPA without converting API or asset misses into HTML 200s."""

    def __init__(self, *, directory: Path, reserved_roots: Collection[str]) -> None:
        super().__init__(directory=directory, html=True, check_dir=True)
        self._index_path = directory / "index.html"
        self._reserved_roots = frozenset(reserved_roots) | _STATIC_ASSET_ROOTS

    def _eligible_for_index(self, path: str, scope: Scope) -> bool:
        if scope.get("method") not in {"GET", "HEAD"}:
            return False
        original_path = scope.get("path")
        if not isinstance(original_path, str) or not _safe_extensionless_path(original_path):
            return False
        if not _accepts_html(scope) or not _safe_extensionless_path(path):
            return False
        first = next((segment for segment in path.split("/") if segment), "")
        return bool(first) and first not in self._reserved_roots and self._index_path.is_file()

    def _index_response(self) -> FileResponse:
        return FileResponse(self._index_path, media_type="text/html")

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            response = await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or not self._eligible_for_index(path, scope):
                raise
            return self._index_response()

        if response.status_code == 404 and self._eligible_for_index(path, scope):
            return self._index_response()
        return response
