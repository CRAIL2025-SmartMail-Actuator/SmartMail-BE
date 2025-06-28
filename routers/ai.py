from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import schemas
import crud
import models
from database import get_db
from auth import get_current_user
import time

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/generate-response", response_model=schemas.StandardResponse)
async def generate_ai_response(
    request: schemas.AIResponseRequest,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify email belongs to user
    email = await crud.get_email(db, request.email_id, current_user.id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Simulate AI response generation
    start_time = time.time()

    # Create AI response record
    response_data = {
        "email_id": request.email_id,
        "suggestion": "Dear Customer,\n\nThank you for reaching out regarding your inquiry...",
        "confidence": 0.92,
        "tone": request.preferences.get("tone", "professional")
        if request.preferences
        else "professional",
        "reasoning": "High confidence due to clear context. Used professional tone to match customer service standards.",
        "alternative_suggestions": [
            {
                "suggestion": "Hi there,\n\nI'd be happy to help with your question...",
                "tone": "friendly",
                "confidence": 0.87,
            }
        ],
        "used_documents": ["doc_123", "doc_456"],
        "processing_time_ms": int((time.time() - start_time) * 1000),
    }

    db_response = await crud.create_ai_response(db, response_data)

    return schemas.StandardResponse(
        success=True,
        data={
            "response_id": db_response.id,
            "suggestion": db_response.suggestion,
            "confidence": db_response.confidence,
            "category": email.category.name if email.category else "General",
            "tone": db_response.tone,
            "reasoning": db_response.reasoning,
            "alternative_suggestions": db_response.alternative_suggestions or [],
            "used_documents": db_response.used_documents or [],
            "processing_time_ms": db_response.processing_time_ms,
        },
    )


@router.get("/responses", response_model=schemas.StandardResponse)
async def get_ai_responses(
    email_id: Optional[str] = None,
    confidence_min: Optional[float] = None,
    page: int = 1,
    limit: int = 20,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Implementation would filter and return AI responses
    return schemas.StandardResponse(
        success=True,
        data={
            "responses": [],
            "pagination": {"current_page": page, "total_pages": 1, "total_items": 0},
        },
    )


@router.post(
    "/responses/{response_id}/approve", response_model=schemas.StandardResponse
)
async def approve_ai_response(
    response_id: str,
    approval_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Implementation would approve and optionally send response
    return schemas.StandardResponse(
        success=True, data={"message": "Response approved and sent"}
    )


@router.post("/responses/{response_id}/reject", response_model=schemas.StandardResponse)
async def reject_ai_response(
    response_id: str,
    rejection_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Implementation would reject response and log feedback
    return schemas.StandardResponse(success=True, data={"message": "Response rejected"})
