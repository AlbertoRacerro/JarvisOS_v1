from app.core.database import open_sqlite_connection
from app.modules.events.service import log_event
from app.modules.secrets.models import ScalewaySecretStatus
from app.modules.secrets.storage import (
    ENV_SOURCE,
    PERSISTED_CORRUPTED,
    PERSISTED_SOURCE,
    PERSISTED_UNAVAILABLE,
    EffectiveSecret,
    SecretEnvironmentOverrideError,
    SecretStorageError,
    SecretStorageUnavailableError,
    delete_persisted_scaleway_api_key,
    get_effective_scaleway_api_key,
    normalize_scaleway_api_key,
    set_persisted_scaleway_api_key,
)


def read_scaleway_secret_status(*, log_status_check: bool = False) -> ScalewaySecretStatus:
    status = _status_from_secret(get_effective_scaleway_api_key())
    if log_status_check:
        _log_secret_event(
            "ScalewayApiKeyStatusChecked",
            "scaleway_key_status_checked",
            status,
        )
    return status


def save_scaleway_api_key(api_key: str | None) -> ScalewaySecretStatus:
    normalized = normalize_scaleway_api_key(api_key)
    secret = set_persisted_scaleway_api_key(normalized)
    status = _status_from_secret(secret)
    _log_secret_event("ScalewayApiKeySaved", "scaleway_key_saved", status)
    return status


def delete_scaleway_api_key() -> ScalewaySecretStatus:
    secret = delete_persisted_scaleway_api_key()
    status = _status_from_secret(secret)
    _log_secret_event("ScalewayApiKeyDeleted", "scaleway_key_deleted", status)
    return status


def _status_from_secret(secret: EffectiveSecret) -> ScalewaySecretStatus:
    if secret.source == ENV_SOURCE and secret.key_present:
        effective_source = "environment"
        storage_mode = "environment"
    elif secret.source == PERSISTED_SOURCE and secret.key_present:
        effective_source = "secure_persisted"
        storage_mode = "secure_persisted"
    else:
        effective_source = "none"
        if secret.persisted_state == PERSISTED_CORRUPTED:
            storage_mode = "corrupted"
        elif secret.persisted_state == PERSISTED_UNAVAILABLE:
            storage_mode = "unavailable"
        else:
            storage_mode = "none"

    return ScalewaySecretStatus(
        key_present=secret.key_present,
        source=secret.source,
        effective_source=effective_source,
        persisted_state=secret.persisted_state,
        masked_preview=None,
        last_updated_at=secret.last_updated_at,
        storage_mode=storage_mode,
        reason_code=secret.reason_code,
    )


def _log_secret_event(
    event_type: str,
    action: str,
    status: ScalewaySecretStatus,
) -> None:
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
                "effective_source": status.effective_source,
                "persisted_state": status.persisted_state,
                "storage_mode": status.storage_mode,
                "reason_code": status.reason_code,
                "last_updated_at": status.last_updated_at,
            },
        )
        connection.commit()


__all__ = [
    "SecretEnvironmentOverrideError",
    "SecretStorageError",
    "SecretStorageUnavailableError",
    "delete_scaleway_api_key",
    "normalize_scaleway_api_key",
    "read_scaleway_secret_status",
    "save_scaleway_api_key",
]
