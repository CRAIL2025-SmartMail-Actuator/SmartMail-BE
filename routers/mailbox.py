from datetime import datetime
import imaplib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import schemas
import models
from database import get_db
from auth import get_current_user
from .moniter import manager as monitor_manager

router = APIRouter(prefix="/mailbox", tags=["Mailbox"])


@router.post("/configure", response_model=schemas.StandardResponse)
async def configure_mailbox(
    config: schemas.MailboxConfigCreate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check if a mailbox with the same email already exists for the user
    result = await db.execute(
        select(models.MailboxConfig).where(
            models.MailboxConfig.user_id == current_user.id,
            models.MailboxConfig.email == config.email,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="This email is already configured")

    # Create new mailbox config
    new_config = models.MailboxConfig(
        user_id=current_user.id,
        email=config.email,
        app_password=config.app_password,
        auto_reply_emails=config.auto_reply_emails,
        confidence_threshold=config.confidence_threshold,
        enabled=False,
        connection_status="connected",
        last_sync=None,
    )

    db.add(new_config)
    await db.commit()
    await db.refresh(new_config)

    return schemas.StandardResponse(
        success=True,
        data={
            "id": new_config.id,
            "email": new_config.email,
            "connection_status": new_config.connection_status,
            "last_sync": new_config.last_sync,
            "auto_reply_emails": new_config.auto_reply_emails,
            "confidence_threshold": new_config.confidence_threshold,
            "enabled": new_config.enabled,
        },
    )


@router.post("/test-connection", response_model=schemas.StandardResponse)
async def test_mailbox_connection(
    connection_test: schemas.MailboxConnectionTest,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Attempt Gmail IMAP login
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(connection_test.email, connection_test.app_password)
        mail.logout()

        # Fetch the mailbox config for this user & email
        result = await db.execute(
            select(models.MailboxConfig).where(
                models.MailboxConfig.user_id == current_user.id,
                models.MailboxConfig.email == connection_test.email,
            )
        )
        mailbox = result.scalar_one_or_none()

        if mailbox:
            # Update existing
            mailbox.connection_status = "connected"
            mailbox.last_sync = datetime.utcnow()
        else:
            # Create new MailboxConfig
            new_config = models.MailboxConfig(
                user_id=current_user.id,
                email=connection_test.email,
                app_password=connection_test.app_password,
                auto_reply_emails=[],
                confidence_threshold=0.8,
                enabled=False,
                connection_status="connected",
                last_sync=datetime.utcnow(),
            )
            db.add(new_config)

        await db.commit()

        return schemas.StandardResponse(
            success=True,
            data={
                "connection_status": "success",
                "message": "Successfully connected to Gmail",
            },
        )

    except Exception as e:
        return schemas.StandardResponse(
            success=False,
            data={"connection_status": "failed", "message": str(e)},
        )


@router.get("/configuration", response_model=schemas.StandardResponse)
async def get_mailbox_configuration(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.MailboxConfig).where(
            models.MailboxConfig.user_id == current_user.id
        )
    )
    configs = result.scalars().all()

    if not configs:
        raise HTTPException(status_code=400, detail="No mailbox configurations found")

    return schemas.StandardResponse(
        success=True,
        data=[
            {
                "id": config.id,
                "email": config.email,
                "connection_status": config.connection_status,
                "auto_reply_emails": config.auto_reply_emails,
                "confidence_threshold": config.confidence_threshold,
                "enabled": config.enabled,
                "monitoring_status": monitor_manager.is_monitoring(config.id),
                "auto_reply_enabled": config.auto_reply_enabled,
            }
            for config in configs
        ],
    )


@router.patch(
    "/{mailbox_id}/toggle-auto-reply", response_model=schemas.StandardResponse
)
async def toggle_auto_reply_enabled(
    mailbox_id: int,
    toggle_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.MailboxConfig).where(models.MailboxConfig.id == mailbox_id)
    )
    mailbox = result.scalar_one_or_none()

    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")

    if mailbox.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    mailbox.auto_reply_enabled = not mailbox.auto_reply_enabled
    await db.commit()
    await db.refresh(mailbox)

    return schemas.StandardResponse(
        success=True,
        data={
            "message": f"Auto-reply {'enabled' if mailbox.auto_reply_enabled else 'disabled'} successfully"
        },
    )
