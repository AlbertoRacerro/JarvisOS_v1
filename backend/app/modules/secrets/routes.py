from fastapi import APIRouter, HTTPException, Request

from app.modules.secrets.models import ScalewaySecretStatus
from app.modules.secrets.service import (
    delete_scaleway_api_key,
    read_scaleway_secret_status,
    save_scaleway_api_key,
)

router = APIRouter(prefix="/secrets", tags=["secrets"])


@router.get("/scaleway/status", response_model=ScalewaySecretStatus)
def get_scaleway_status() -> ScalewaySecretStatus:
    return read_scaleway_secret_status(log_status_check=True)


@router.post("/scaleway/api-key", response_model=ScalewaySecretStatus)
async def set_scaleway_api_key(request: Request) -> ScalewaySecretStatus:
    try:
        payload = await request.json()
    except ValueError:
        payload = None
    api_key = payload.get("api_key") if isinstance(payload, dict) else None
    try:
        return save_scaleway_api_key(api_key if isinstance(api_key, str) else None)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "scaleway_api_key_invalid",
                "message": "Scaleway API key must be a non-empty single token.",
            },
        ) from None


@router.delete("/scaleway/api-key", response_model=ScalewaySecretStatus)
def remove_scaleway_api_key() -> ScalewaySecretStatus:
    return delete_scaleway_api_key()
