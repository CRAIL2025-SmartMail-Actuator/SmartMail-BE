from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import schemas
import crud
import models
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=schemas.StandardResponse)
async def get_categories(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    categories = await crud.get_categories(db, current_user.id)
    return schemas.StandardResponse(
        success=True,
        data=[schemas.CategoryResponse.model_validate(cat) for cat in categories],
    )


@router.post("", response_model=schemas.StandardResponse)
async def create_category(
    category: schemas.CategoryCreate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    db_category = await crud.create_category(db, category, current_user.id)
    return schemas.StandardResponse(
        success=True, data=schemas.CategoryResponse.model_validate(db_category)
    )


@router.put("/{category_id}", response_model=schemas.StandardResponse)
async def update_category(
    category_id: int,
    category: schemas.CategoryUpdate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    db_category = await crud.update_category(db, category_id, current_user.id, category)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    return schemas.StandardResponse(
        success=True, data=schemas.CategoryResponse.model_validate(db_category)
    )


@router.delete("/{category_id}", response_model=schemas.StandardResponse)
async def delete_category(
    category_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await crud.delete_category(db, category_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")

    return schemas.StandardResponse(
        success=True, data={"message": "Category deleted successfully"}
    )
