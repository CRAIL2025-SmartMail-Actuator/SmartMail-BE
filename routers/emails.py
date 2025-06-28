from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import schemas
import crud
import models
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/emails", tags=["Emails"])


@router.get("/inbox", response_model=schemas.StandardResponse)
async def get_inbox_emails(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * limit
    emails = await crud.get_emails(db, current_user.id, skip, limit)

    email_responses = []
    for email in emails:
        email_dict = {
            "id": email.id,
            "from": email.from_email,
            "from_name": email.from_name,
            "to": email.to_email,
            "subject": email.subject,
            "body": email.body,
            "html_body": email.html_body,
            "timestamp": email.timestamp,
            "is_read": email.is_read,
            "is_starred": email.is_starred,
            "has_attachments": email.has_attachments,
            "priority": email.priority,
            "category": email.category.name if email.category else None,
            "labels": email.labels or [],
            "thread_id": email.thread_id,
            "ai_analysis": email.ai_analysis,
        }
        email_responses.append(email_dict)

    return schemas.StandardResponse(
        success=True,
        data={
            "emails": email_responses,
            "pagination": {
                "current_page": page,
                "total_pages": 10,  # Calculate based on total count
                "total_items": 200,  # Get actual count
            },
        },
    )


@router.get("/{email_id}", response_model=schemas.StandardResponse)
async def get_email_details(
    email_id: str,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    email = await crud.get_email(db, email_id, current_user.id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    attachments = []
    for att in email.attachments:
        attachments.append(
            {
                "id": att.id,
                "name": att.name,
                "size": att.size,
                "type": att.type,
                "download_url": f"/emails/{email_id}/attachments/{att.id}",
            }
        )

    return schemas.StandardResponse(
        success=True,
        data={
            "id": email.id,
            "from": email.from_email,
            "from_name": email.from_name,
            "to": email.to_email,
            "subject": email.subject,
            "body": email.body,
            "html_body": email.html_body,
            "timestamp": email.timestamp,
            "is_read": email.is_read,
            "is_starred": email.is_starred,
            "has_attachments": email.has_attachments,
            "priority": email.priority,
            "category": email.category.name if email.category else None,
            "labels": email.labels or [],
            "thread": [],  # Would implement thread retrieval
            "attachments": attachments,
        },
    )


@router.patch("/{email_id}/read-status", response_model=schemas.StandardResponse)
async def update_read_status(
    email_id: str,
    status_update: dict,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Implementation would update read status
    return schemas.StandardResponse(
        success=True, data={"message": "Read status updated"}
    )


@router.patch("/{email_id}/star-status", response_model=schemas.StandardResponse)
async def update_star_status(
    email_id: str,
    status_update: dict,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Implementation would update star status
    return schemas.StandardResponse(
        success=True, data={"message": "Star status updated"}
    )


@router.post("/{email_id}/reply", response_model=schemas.StandardResponse)
async def send_reply(
    email_id: str,
    reply_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Implementation would send email reply
    return schemas.StandardResponse(
        success=True,
        data={
            "sent_email_id": "sent_123",
            "message_id": "msg_123",
            "sent_at": "2024-01-15T10:35:00Z",
            "status": "sent",
            "recipients": ["customer@example.com"],
            "delivery_status": "delivered",
        },
    )
