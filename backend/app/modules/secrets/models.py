from pydantic import BaseModel


class ScalewaySecretStatus(BaseModel):
    key_present: bool
    source: str
    masked_preview: str | None = None
    last_updated_at: str | None = None
    storage_mode: str = "runtime_memory"
