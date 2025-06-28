from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List
import models
import schemas
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# User CRUD
async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.User:
    db_user = models.User(
        name=user.name,
        email=user.email,
        domain=user.domain,
        hashed_password=get_password_hash(user.password),
    )
    db.add(db_user)
    await db.flush()
    return db_user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[models.User]:
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    return result.scalar_one_or_none()


# Category CRUD
async def create_category(
    db: AsyncSession, category: schemas.CategoryCreate, user_id: int
) -> models.Category:
    db_category = models.Category(user_id=user_id, **category.model_dump())
    db.add(db_category)
    await db.flush()
    return db_category


async def get_categories(db: AsyncSession, user_id: int) -> List[models.Category]:
    result = await db.execute(
        select(models.Category).where(models.Category.user_id == user_id)
    )
    return result.scalars().all()


async def get_category(
    db: AsyncSession, category_id: int, user_id: int
) -> Optional[models.Category]:
    result = await db.execute(
        select(models.Category).where(
            and_(models.Category.id == category_id, models.Category.user_id == user_id)
        )
    )
    return result.scalar_one_or_none()


async def update_category(
    db: AsyncSession,
    category_id: int,
    user_id: int,
    category_update: schemas.CategoryUpdate,
) -> Optional[models.Category]:
    await db.execute(
        update(models.Category)
        .where(
            and_(models.Category.id == category_id, models.Category.user_id == user_id)
        )
        .values(**category_update.model_dump(exclude_unset=True))
    )
    return await get_category(db, category_id, user_id)


async def delete_category(db: AsyncSession, category_id: int, user_id: int) -> bool:
    result = await db.execute(
        delete(models.Category).where(
            and_(models.Category.id == category_id, models.Category.user_id == user_id)
        )
    )
    return result.rowcount > 0


# Document CRUD
async def create_document(
    db: AsyncSession, name: str, doc_type: str, size: int, user_id: int
) -> models.Document:
    db_document = models.Document(
        user_id=user_id,
        name=name,
        type=doc_type,
        size=size,
    )
    db.add(db_document)
    await db.flush()
    return db_document


async def get_documents(
    db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20
) -> List[models.Document]:
    result = await db.execute(
        select(models.Document)
        .where(models.Document.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .options(selectinload(models.Document.document_categories))
    )
    return result.scalars().all()


# Email CRUD
async def create_email(
    db: AsyncSession, email_data: dict, user_id: int
) -> models.Email:
    db_email = models.Email(user_id=user_id, **email_data)
    db.add(db_email)
    await db.flush()
    return db_email


async def get_emails(
    db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20
) -> List[models.Email]:
    result = await db.execute(
        select(models.Email)
        .where(models.Email.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .options(selectinload(models.Email.attachments))
    )
    return result.scalars().all()


async def get_email(
    db: AsyncSession, email_id: str, user_id: int
) -> Optional[models.Email]:
    result = await db.execute(
        select(models.Email)
        .where(and_(models.Email.id == email_id, models.Email.user_id == user_id))
        .options(
            selectinload(models.Email.attachments),
            selectinload(models.Email.ai_responses),
        )
    )
    return result.scalar_one_or_none()


# AI Response CRUD
async def create_ai_response(
    db: AsyncSession, response_data: dict
) -> models.AIResponse:
    db_response = models.AIResponse(id=f"resp_{uuid.uuid4().hex[:8]}", **response_data)
    db.add(db_response)
    await db.flush()
    return db_response


# Auto Reply Rule CRUD
async def create_auto_reply_rule(
    db: AsyncSession, rule: schemas.AutoReplyRuleCreate, user_id: int
) -> models.AutoReplyRule:
    db_rule = models.AutoReplyRule(
        user_id=user_id,
        **rule.model_dump(exclude={"categories"}),
    )
    db.add(db_rule)
    await db.flush()
    return db_rule


async def get_auto_reply_rules(
    db: AsyncSession, user_id: int
) -> List[models.AutoReplyRule]:
    result = await db.execute(
        select(models.AutoReplyRule).where(models.AutoReplyRule.user_id == user_id)
    )
    return result.scalars().all()


# Activity Log CRUD
async def create_activity_log(
    db: AsyncSession, log_data: dict, user_id: int
) -> models.ActivityLog:
    db_log = models.ActivityLog(user_id=user_id, **log_data)
    db.add(db_log)
    await db.flush()
    return db_log


async def get_activity_logs(
    db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20
) -> List[models.ActivityLog]:
    result = await db.execute(
        select(models.ActivityLog)
        .where(models.ActivityLog.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(models.ActivityLog.timestamp.desc())
    )
    return result.scalars().all()
