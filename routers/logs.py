from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import schemas
import crud
import models
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("", response_model=schemas.StandardResponse)
async def get_activity_logs(
    type: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    confidence_min: Optional[float] = Query(None),
    confidence_max: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * limit
    logs = await crud.get_activity_logs(db, current_user.id, skip, limit)

    log_responses = [schemas.ActivityLogResponse.model_validate(log) for log in logs]

    return schemas.StandardResponse(
        success=True,
        data={
            "logs": log_responses,
            "pagination": {
                "current_page": page,
                "total_pages": 50,  # Calculate based on total count
                "total_items": 1000,  # Get actual count
            },
        },
    )


@router.get("/export")
async def export_logs(
    format: str = Query("csv"),
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Implementation would export logs in specified format
    return {"message": "Export functionality would be implemented here"}
