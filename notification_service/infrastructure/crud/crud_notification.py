from datetime import datetime
from typing import Optional
from typing import Sequence
from uuid import UUID

from notification_registry import NotificationChannel
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from utils_library.AlchemyRepository import crud

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

    async def get(self, *, id: UUID, ignore_deleted: bool = True) -> Optional[NotificationTable]:
        stmt = select(NotificationTable).where(NotificationTable.id == id)
        results = await self.get_multi(query=stmt, limit=1, ignore_deleted=ignore_deleted)
        return results[0] if results else None

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

    def _list_filters(
        self,
        *,
        recipient_id: UUID | None = None,
        status: NotificationStatus | None = None,
        channel: NotificationChannel | None = None,
    ) -> list:
        filters = []
        if recipient_id is not None:
            filters.append(NotificationTable.recipient_id == recipient_id)
        if status is not None:
            filters.append(NotificationTable.status == status)
        if channel is not None:
            filters.append(NotificationTable.channel == channel)
        return filters

    async def list_notifications(
        self,
        *,
        recipient_id: UUID | None = None,
        status: NotificationStatus | None = None,
        channel: NotificationChannel | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[NotificationTable]:
        stmt = select(NotificationTable).where(
            *self._list_filters(
                recipient_id=recipient_id,
                status=status,
                channel=channel,
            )
        )
        if hasattr(NotificationTable, "created_at"):
            stmt = stmt.order_by(NotificationTable.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.exec(stmt)
        return result.all()

    async def count_notifications(
        self,
        *,
        recipient_id: UUID | None = None,
        status: NotificationStatus | None = None,
        channel: NotificationChannel | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(NotificationTable).where(
            *self._list_filters(
                recipient_id=recipient_id,
                status=status,
                channel=channel,
            )
        )
        result = await self.session.exec(stmt)
        return int(result.one())

    async def update_status(
        self,
        notification_id: UUID,
        status: NotificationStatus,
        error_message: Optional[str] = None,
    ) -> Optional[NotificationTable]:
        notification = await self.get(id=notification_id)
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

