from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.usage import UsageResponse
from app.services.usage_service import get_usage

router = APIRouter(tags=["usage"])


@router.get("/usage", response_model=UsageResponse)
def usage_report(
    api_key: str = Query(..., description="API key to aggregate"),
    from_: datetime = Query(..., alias="from", description="ISO8601 start (inclusive)"),
    to: datetime = Query(..., description="ISO8601 end (inclusive)"),
    group_by: str = Query("day", pattern="^(day|model)$"),
    db: Session = Depends(get_db),
) -> UsageResponse:
    if from_ > to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'from' must be before or equal to 'to'",
        )
    return get_usage(db, api_key, from_, to, group_by)
