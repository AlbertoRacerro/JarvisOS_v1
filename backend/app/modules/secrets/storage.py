import os
from dataclasses import dataclass, field

from app.core.paths import build_paths
from app.modules.events.service import utc_now

SCALEWAY_API_KEY_ENV_VAR = "SCALEWAY_API_KEY"
RUNTIME_MEMORY_SOURCE = "runtime_memory"
ENV_SOURCE = "env"
NONE_SOURCE = "none"


@dataclass(frozen=True, repr=False)
class RuntimeSecret:
    value: str
    last_updated_at: str


@dataclass(frozen=True)
class EffectiveSecret:
    value: str | None = field(repr=False)
    source: str
    last_updated_at: str | None = None

    @property
    def key_present(self) -> bool:
        return bool(self.value)


_runtime_scaleway_api_keys: dict[str, RuntimeSecret] = {}


def get_effective_scaleway_api_key() -> EffectiveSecret:
    env_value = os.getenv(SCALEWAY_API_KEY_ENV_VAR)
    if env_value:
        return EffectiveSecret(value=env_value, source=ENV_SOURCE, last_updated_at=None)

    runtime_secret = _runtime_scaleway_api_keys.get(_storage_namespace())
    if runtime_secret:
        return EffectiveSecret(
            value=runtime_secret.value,
            source=RUNTIME_MEMORY_SOURCE,
            last_updated_at=runtime_secret.last_updated_at,
        )

    return EffectiveSecret(value=None, source=NONE_SOURCE, last_updated_at=None)


def set_runtime_scaleway_api_key(api_key: str) -> EffectiveSecret:
    secret = RuntimeSecret(value=api_key, last_updated_at=utc_now())
    _runtime_scaleway_api_keys[_storage_namespace()] = secret
    return get_effective_scaleway_api_key()


def delete_runtime_scaleway_api_key() -> EffectiveSecret:
    _runtime_scaleway_api_keys.pop(_storage_namespace(), None)
    return get_effective_scaleway_api_key()


def _storage_namespace() -> str:
    return str(build_paths().data_root.resolve())
