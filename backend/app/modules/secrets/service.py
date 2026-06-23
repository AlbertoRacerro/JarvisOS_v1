from app.core.database import open_sqlite_connection
from app.modules.events.service import log_event
from app.modules.secrets.models import ScalewaySecretStatus
from app.modules.secrets.storage import (
    EffectiveSecret,
    delete_runtime_scaleway_api_key,
    get_effective_scaleway_api_key,
    set_runtime_scaleway_api_key,
)

MAX_SCALEWAY_API_KEY_LENGTH = 4096


def read_scaleway_secret_status(*, log_status_check: bool = False) -> ScalewaySecretStatus:
    secret = get_effective_scaleway_api_key()
    status = _status_from_secret(secret)
    if log_status_check:
        _log_secret_event("ScalewayApiKeyStatusChecked", "scaleway_key_status_checked", status)
    return status


def save_scaleway_api_key(api_key: str | None) -> ScalewaySecretStatus:
    secret = set_runtime_scaleway_api_key(normalize_scaleway_api_key(api_key))
    status = _status_from_secret(secret)
    _log_secret_event("ScalewayApiKeySaved", "scaleway_key_saved", status)
    return status


def delete_scaleway_api_key() -> ScalewaySecretStatus:
    secret = delete_runtime_scaleway_api_key()
    status = _status_from_secret(secret)
    _log_secret_event("ScalewayApiKeyDeleted", "scaleway_key_deleted", status)
    return status


def normalize_scaleway_api_key(api_key: str | None) -> str:
    stripped = (api_key or "").strip()
    if not stripped:
        raise ValueError("empty")
    if len(stripped) > MAX_SCALEWAY_API_KEY_LENGTH:
        raise ValueError("too_long")
    if any(character.isspace() for character in stripped):
        raise ValueError("contains_whitespace")
    return stripped


def _status_from_secret(secret: EffectiveSecret) -> ScalewaySecretStatus:
    return ScalewaySecretStatus(
        key_present=secret.key_present,
        source=secret.source,
        masked_preview=_masked_preview(secret.value),
        last_updated_at=secret.last_updated_at,
    )


def _masked_preview(api_key: str | None) -> str | None:
    if not api_key:
        return None
    if len(api_key) <= 8:
        return "..." + api_key[-4:]
    prefix = api_key[:3]
    suffix = api_key[-4:]
    return f"{prefix}...{suffix}"


def _log_secret_event(event_type: str, action: str, status: ScalewaySecretStatus) -> None:
    with open_sqlite_connection() as connection:
        log_event(
            connection,
            event_type=event_type,
            actor="local-user",
            target_type="ScalewayApiKey",
            target_id=None,
            workspace_id=None,
            payload={
                "action": action,
                "key_present": status.key_present,
                "source": status.source,
                "storage_mode": status.storage_mode,
                "last_updated_at": status.last_updated_at,
            },
        )
        connection.commit()
