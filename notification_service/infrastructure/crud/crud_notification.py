from datetime import datetime
from typing import Optional
from typing import Sequence
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from utils_library.AlchemyRepository import crud

from notification_service.infrastructure.enums import NotificationChannel
from notification_service.infrastructure.enums import NotificationStatus
from notification_service.infrastructure.models import NotificationTable


class CRUDNotification(
    crud.CRUDBaseCreate[NotificationTable],
    crud.CRUDBaseSelect[NotificationTable],
    crud.CRUDBaseDelete[NotificationTable],
    crud.CRUDBaseUpdate[NotificationTable],
):
    def __init__(self, model: type[NotificationTable], session: AsyncSession):
        crud.CRUDBaseCreate.__init__(self, model, session)
        crud.CRUDBaseSelect.__init__(self, model, session)
        crud.CRUDBaseDelete.__init__(self, model, session)
        crud.CRUDBaseUpdate.__init__(self, model, session)

    async def get_by_recipient_id(
        self, recipient_id: UUID, limit: int = 100
    ) -> Sequence[NotificationTable]:
        stmt = select(NotificationTable).where(
            NotificationTable.recipient_id == recipient_id
        )
        return await self.get_multi(query=stmt, limit=limit)

    async def get_by_external_id(
        self, external_id: str
    ) -> Optional[NotificationTable]:
        stmt = select(NotificationTable).where(
            NotificationTable.external_id == external_id
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_pending_notifications(
        self, channel: NotificationChannel, limit: int = 100
    ) -> Sequence[NotificationTable]:
        now = datetime.utcnow()
        stmt = select(NotificationTable).where(
            NotificationTable.status == NotificationStatus.PENDING,
            NotificationTable.channel == channel,
            (NotificationTable.scheduled_at.is_(None))
            | (NotificationTable.scheduled_at <= now),
        )
        return await self.get_multi(query=stmt, limit=limit)

    async def get_failed_for_retry(
        self, channel: NotificationChannel, limit: int = 100
    ) -> Sequence[NotificationTable]:
        now = datetime.utcnow()
        stmt = select(NotificationTable).where(
            NotificationTable.status == NotificationStatus.FAILED,
            NotificationTable.channel == channel,
            NotificationTable.retry_count < NotificationTable.max_retries,
            NotificationTable.next_retry_at.is_not(None),
            NotificationTable.next_retry_at <= now,
        )
        return await self.get_multi(query=stmt, limit=limit)

    async def get_by_status(
        self, status: NotificationStatus, limit: int = 100
    ) -> Sequence[NotificationTable]:
        stmt = select(NotificationTable).where(NotificationTable.status == status)
        return await self.get_multi(query=stmt, limit=limit)

    async def update_status(
        self,
        notification_id: UUID,
        status: NotificationStatus,
        error_message: Optional[str] = None,
    ) -> Optional[NotificationTable]:
        notification = await self.get(notification_id)
        if notification is None:
            return None

        notification.status = status
        if error_message:
            notification.last_error = error_message

        if status == NotificationStatus.SENT:
            notification.sent_at = datetime.utcnow()
        elif status == NotificationStatus.DELIVERED:
            notification.delivered_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(notification)
        return notification


