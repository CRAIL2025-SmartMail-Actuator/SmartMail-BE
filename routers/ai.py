from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .ai_service import ai_reponse
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
    # Initialize ai_res with a default value
    ai_res = None
    
    # Verify email belongs to user
    try:
        email = await crud.get_email(db, request.email_id, current_user.id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Simulate AI response generation
        start_time = time.time()
        print(f"Generating AI response for email ID: {request.email_id}")
        print(f"Email Subject: {email.subject}")
        
        ai_res = ai_reponse(current_user.id, "user", current_user.email, email.subject, email.body)
        
    except HTTPException:
        # Re-raise HTTP exceptions (like email not found)
        raise
    except Exception as e:
        print(f"Error generating AI response: {e}")
        print(f"Traceback: {e.__traceback__}")
        # Handle the error appropriately
        raise HTTPException(
            status_code=500, 
            detail="Failed to generate AI response"
        )
    
    # Check if ai_res was successfully generated
    if ai_res is None:
        raise HTTPException(
            status_code=500,
            detail="AI response generation failed"
        )
    
    response_data = ai_res
    # db_response = await crud.create_ai_response(db, response_data)
    
    return schemas.StandardResponse(
        success=True,
        data=response_data,
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
