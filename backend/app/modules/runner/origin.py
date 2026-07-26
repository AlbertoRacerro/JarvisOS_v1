from fastapi import HTTPException, Request

from app.core.config import get_settings

_MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def require_allowed_mutating_origin(request: Request) -> None:
    """Reject browser-originated mutations from origins outside the CORS allowlist.

    Missing Origin remains valid for loopback-native clients. This is a browser/CSRF
    guard only; it is not authentication and must not be represented as one.
    """

    if request.method.upper() not in _MUTATING_METHODS:
        return
    origin = request.headers.get("origin")
    if origin is None:
        return
    if origin not in get_settings().cors_origins:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "runner_origin_forbidden",
                "message": "The request Origin is not allowed for runner mutations.",
            },
        )
