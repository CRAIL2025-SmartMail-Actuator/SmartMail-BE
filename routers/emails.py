from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import schemas
import crud
import models
from database import get_db
from auth import get_current_user
from sqlalchemy.orm import selectinload

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

    # Use eager loading to load categories with emails
    query = (
        select(models.Email)
        .options(selectinload(models.Email.category))  # Eager load category
        .filter(models.Email.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(models.Email.timestamp.desc())  # Add ordering
    )

    result = await db.execute(query)
    emails = result.scalars().all()

    # Get total count for pagination
    count_query = select(func.count(models.Email.id)).filter(
        models.Email.user_id == current_user.id
    )
    count_result = await db.execute(count_query)
    total_count = count_result.scalar()

    total_pages = (total_count + limit - 1) // limit  # Calculate total pages

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
                "total_pages": total_pages,
                "total_items": total_count,
            },
        },
    )


@router.get("/sent", response_model=schemas.StandardResponse)
async def get_sent_emails(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * limit

    # Fetch sent emails for the user
    sent_emails = await db.execute(
        select(models.SentEmail)
        .where(models.SentEmail.user_id == current_user.id)
        .order_by(models.SentEmail.sent_at.desc())
        .offset(skip)
        .limit(limit)
    )
    sent_email_records = sent_emails.scalars().all()

    # Optional search filter
    if search:
        sent_email_records = [
            email
            for email in sent_email_records
            if search.lower() in email.subject.lower()
            or search.lower() in (email.content or "")
        ]

    email_responses = []
    for email in sent_email_records:
        email_responses.append(
            {
                "id": email.id,
                "to": email.recipients,
                "subject": email.subject
                if hasattr(email, "subject")
                else "",  # fallback
                "content": email.content,
                "html_content": email.html_content,
                "sent_at": email.sent_at,
                "status": email.status,
                "delivery_status": email.delivery_status,
            }
        )

    # Optional: compute total count for pagination
    total = len(email_responses)
    total_pages = (total // limit) + (1 if total % limit else 0)

    return schemas.StandardResponse(
        success=True,
        data={
            "emails": email_responses,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total,
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
    email_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(
            select(models.Email).where(
                models.Email.id == email_id,
                models.Email.user_id == current_user.id,
            )
        )
        email = result.scalar_one_or_none()
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        email.is_read = True
        await db.commit()

        return schemas.StandardResponse(
            success=True,
            data={"message": "Read status set to true", "is_read": True},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{email_id}/star-status", response_model=schemas.StandardResponse)
async def update_star_status(
    email_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(
            select(models.Email).where(
                models.Email.id == email_id,
                models.Email.user_id == current_user.id,
            )
        )
        email = result.scalar_one_or_none()
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")

        email.is_starred = True
        await db.commit()

        return schemas.StandardResponse(
            success=True,
            data={"message": "Star status set to true", "is_starred": True},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
