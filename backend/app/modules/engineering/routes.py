from fastapi import APIRouter

from app.modules.engineering.models import EngineeringBoundary
from app.modules.engineering.service import describe_engineering_boundary

router = APIRouter(prefix="/engineering", tags=["engineering"])


@router.get("/boundary")
def engineering_boundary() -> EngineeringBoundary:
    return describe_engineering_boundary()
