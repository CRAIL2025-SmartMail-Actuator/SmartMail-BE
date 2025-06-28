from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import schemas
import crud
from database import get_db
from datetime import timedelta
from auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.StandardResponse)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = await crud.create_user(db, user)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.id}, expires_delta=access_token_expires
    )

    return schemas.StandardResponse(
        success=True,
        data={
            "user": schemas.UserResponse.model_validate(db_user),
            "access_token": access_token,
            "refresh_token": "refresh_token_here",  # Implement refresh token logic
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        },
    )


@router.post("/login", response_model=schemas.StandardResponse)
async def login(
    user_credentials: schemas.UserLogin, db: AsyncSession = Depends(get_db)
):
    print("Login attempt with:", user_credentials.email)
    print("Login attempt with password:", user_credentials.password)
    user = await crud.get_user_by_email(db, email=user_credentials.email)
    if not user or not crud.verify_password(
        user_credentials.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    print({"sub": str(user.id)})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    return schemas.StandardResponse(
        success=True,
        data={
            "user": schemas.UserResponse.model_validate(user),
            "access_token": access_token,
            "refresh_token": "refresh_token_here",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        },
    )
