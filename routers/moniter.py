from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import MailboxConfig, User
from email_service import EmailService
from auth import get_current_user
from threading import Thread
from typing import Dict
import logging

router = APIRouter(prefix="/monitor", tags=["Email Monitor"])

logger = logging.getLogger(__name__)


class EmailMonitorManager:
    def __init__(self):
        self.active_monitors: Dict[int, Thread] = {}
        self.services: Dict[int, EmailService] = {}

    def is_monitoring(self, mailbox_id: int) -> bool:
        return mailbox_id in self.active_monitors

    def start_monitoring(self, mailbox: MailboxConfig, db: AsyncSession):
        if self.is_monitoring(mailbox.id):
            logger.info(f"Already monitoring mailbox {mailbox.email}")
            return

        service = EmailService(mailbox)
        thread = Thread(target=service.start_monitoring, daemon=True)
        self.services[mailbox.id] = service
        self.active_monitors[mailbox.id] = thread

        thread.start()
        logger.info(f"Started monitoring for mailbox {mailbox.email}")

    def stop_monitoring(self, mailbox_id: int):
        if not self.is_monitoring(mailbox_id):
            logger.warning(f"Monitor not running for mailbox ID {mailbox_id}")
            return

        service = self.services[mailbox_id]
        service.stop_monitoring()
        thread = self.active_monitors[mailbox_id]
        thread.join(timeout=5)

        del self.services[mailbox_id]
        del self.active_monitors[mailbox_id]

        logger.info(f"Stopped monitoring mailbox ID {mailbox_id}")


manager = EmailMonitorManager()


@router.post("/start/{mailbox_id}")
async def start_monitoring_mailbox(
    mailbox_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await db.execute(
            select(MailboxConfig).where(MailboxConfig.id == mailbox_id)
        )
        mailbox = result.scalar_one_or_none()

        if not mailbox or not mailbox.enabled:
            raise HTTPException(status_code=404, detail="Mailbox not found or disabled")

        if manager.is_monitoring(mailbox_id):
            return {"message": f"Already monitoring mailbox {mailbox_id}"}

        background_tasks.add_task(manager.start_monitoring, mailbox, db)
        return {"message": f"Started monitoring mailbox {mailbox_id}"}
    except Exception as e:
        logger.error(f"Error starting monitor for mailbox {mailbox_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to start monitoring mailbox"
        )


@router.post("/stop/{mailbox_id}")
def stop_monitoring_mailbox(
    mailbox_id: int,
    current_user: User = Depends(get_current_user),
):
    if not manager.is_monitoring(mailbox_id):
        raise HTTPException(
            status_code=404, detail="Monitor not running for this mailbox"
        )

    manager.stop_monitoring(mailbox_id)
    return {"message": f"Stopped monitoring mailbox {mailbox_id}"}


@router.post("/start-all/{user_id}")
async def start_all_monitors(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MailboxConfig).where(
            MailboxConfig.user_id == user_id, MailboxConfig.enabled
        )
    )
    mailboxes = result.scalars().all()

    if not mailboxes:
        raise HTTPException(
            status_code=404, detail="No enabled mailboxes found for user"
        )

    started = 0
    for mailbox in mailboxes:
        if not manager.is_monitoring(mailbox.id):
            background_tasks.add_task(manager.start_monitoring, mailbox, db)
            started += 1

    return {
        "message": f"Started monitoring {started} out of {len(mailboxes)} mailboxes"
    }


@router.post("/stop-all/{user_id}")
async def stop_all_monitors(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MailboxConfig).where(MailboxConfig.user_id == user_id)
    )
    mailboxes = result.scalars().all()

    stopped = 0
    for mailbox in mailboxes:
        if manager.is_monitoring(mailbox.id):
            manager.stop_monitoring(mailbox.id)
            stopped += 1

    return {
        "message": f"Stopped monitoring {stopped} out of {len(mailboxes)} mailboxes"
    }
