from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import schemas
import crud
import models
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/auto-reply", tags=["Auto Reply"])


@router.get("/rules", response_model=schemas.StandardResponse)
async def get_auto_reply_rules(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rules = await crud.get_auto_reply_rules(db, current_user.id)
    rule_responses = []

    for rule in rules:
        rule_data = {
            "id": rule.id,
            "email_address": rule.email_address,
            "enabled": rule.enabled,
            "categories": [],  # Would get from relationship
            "confidence_threshold": rule.confidence_threshold,
            "keywords": rule.keywords or [],
            "schedule": rule.schedule,
            "created_at": rule.created_at,
        }
        rule_responses.append(rule_data)

    return schemas.StandardResponse(success=True, data=rule_responses)


@router.post("/rules", response_model=schemas.StandardResponse)
async def create_auto_reply_rule(
    rule: schemas.AutoReplyRuleCreate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    db_rule = await crud.create_auto_reply_rule(db, rule, current_user.id)

    return schemas.StandardResponse(
        success=True, data=schemas.AutoReplyRuleResponse.model_validate(db_rule)
    )


@router.put("/rules/{rule_id}", response_model=schemas.StandardResponse)
async def update_auto_reply_rule(
    rule_id: int,
    rule: schemas.AutoReplyRuleCreate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    db_rule = await crud.get_auto_reply_rule(db, rule_id)
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    for key, value in rule.model_dump(exclude={"categories"}).items():
        setattr(db_rule, key, value)

    await db.commit()
    await db.refresh(db_rule)

    return schemas.StandardResponse(
        success=True, data={"message": "Rule updated successfully"}
    )


@router.delete("/rules/{rule_id}", response_model=schemas.StandardResponse)
async def delete_auto_reply_rule(
    rule_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    db_rule = await crud.get_auto_reply_rule(db, rule_id)
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    await db.delete(db_rule)
    await db.commit()

    return schemas.StandardResponse(
        success=True, data={"message": "Rule deleted successfully"}
    )


@router.patch("/rules/{rule_id}/toggle", response_model=schemas.StandardResponse)
async def toggle_auto_reply_rule(
    rule_id: int,
    toggle_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    enabled = toggle_data.get("enabled")
    if enabled is None:
        raise HTTPException(status_code=400, detail="Missing 'enabled' field")

    db_rule = await crud.get_auto_reply_rule(db, rule_id)
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db_rule.enabled = enabled
    await db.commit()
    await db.refresh(db_rule)

    return schemas.StandardResponse(
        success=True,
        data={"message": f"Rule {'enabled' if enabled else 'disabled'} successfully"},
    )
