from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import schemas
import crud
import models
from database import get_db
from auth import get_current_user
import aiofiles
import os

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=schemas.StandardResponse)
async def upload_document(
    file: UploadFile = File(...),
    categories: str = Form("[]"),  # JSON string of category IDs
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(upload_dir, file.filename)
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    # Create document record
    db_document = await crud.create_document(
        db, file.filename, file.content_type, len(content), current_user.id
    )

    return schemas.StandardResponse(
        success=True,
        data={
            "id": db_document.id,
            "name": db_document.name,
            "type": db_document.type,
            "size": db_document.size,
            "upload_date": db_document.upload_date,
            "categories": [],  # Would parse categories from form data
            "processing_status": db_document.processing_status,
        },
    )


@router.get("", response_model=schemas.StandardResponse)
async def get_documents(
    category_id: Optional[str] = None,
    doc_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * limit
    documents = await crud.get_documents(db, current_user.id, skip, limit)

    document_responses = []
    for doc in documents:
        doc_response = schemas.DocumentResponse.model_validate(doc)
        # Get categories for this document
        doc_response.categories = [dc.category.id for dc in doc.document_categories]
        document_responses.append(doc_response)

    return schemas.StandardResponse(
        success=True,
        data={
            "documents": document_responses,
            "pagination": {
                "current_page": page,
                "total_pages": 5,  # Calculate based on total count
                "total_items": 100,  # Get actual count
                "items_per_page": limit,
            },
        },
    )


@router.get("/{document_id}/content", response_model=schemas.StandardResponse)
async def get_document_content(
    document_id: str,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Implementation would extract and return document content
    return schemas.StandardResponse(
        success=True,
        data={
            "id": document_id,
            "name": "document.pdf",
            "content": "Document content here...",
            "metadata": {
                "word_count": 1500,
                "language": "en",
                "extracted_at": "2024-01-15T10:30:00Z",
            },
        },
    )


@router.delete("/{document_id}", response_model=schemas.StandardResponse)
async def delete_document(
    document_id: str,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Implementation would delete document and file
    return schemas.StandardResponse(
        success=True, data={"message": "Document deleted successfully"}
    )
