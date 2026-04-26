from typing import Optional
from typing import Sequence
from uuid import UUID

from notification_registry import NotificationChannel
from notification_registry import NotificationType
from sqlalchemy.exc import IntegrityError
from sqlmodel import delete
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from utils_library.AlchemyRepository import crud

from notification_service.infrastructure.models import UserNotificationPreferenceTable


class CRUDUserPreference(
    crud.CRUDBaseCreate[UserNotificationPreferenceTable],
    crud.CRUDBaseSelect[UserNotificationPreferenceTable],
    crud.CRUDBaseDelete[UserNotificationPreferenceTable],
    crud.CRUDBaseUpdate[UserNotificationPreferenceTable],
):
    def __init__(self, model: type[UserNotificationPreferenceTable], session: AsyncSession):
        crud.CRUDBaseCreate.__init__(self, model, session)
        crud.CRUDBaseSelect.__init__(self, model, session)
        crud.CRUDBaseDelete.__init__(self, model, session)
        crud.CRUDBaseUpdate.__init__(self, model, session)

    async def get_by_user(self, user_id: UUID) -> Sequence[UserNotificationPreferenceTable]:
        stmt = select(UserNotificationPreferenceTable).where(
            UserNotificationPreferenceTable.user_id == user_id
        )
        return await self.get_multi(query=stmt, limit=1000)

    async def get_by_user_and_type(
        self, user_id: UUID, notification_type: NotificationType
    ) -> Sequence[UserNotificationPreferenceTable]:
        stmt = select(UserNotificationPreferenceTable).where(
            UserNotificationPreferenceTable.user_id == user_id,
            UserNotificationPreferenceTable.notification_type == notification_type,
        )
        return await self.get_multi(query=stmt, limit=100)

    async def get_by_user_and_channel(
        self, user_id: UUID, channel: NotificationChannel
    ) -> Optional[UserNotificationPreferenceTable]:
        stmt = select(UserNotificationPreferenceTable).where(
            UserNotificationPreferenceTable.user_id == user_id,
            UserNotificationPreferenceTable.channel == channel,
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def set_preferences(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        entries: list[UserNotificationPreferenceTable],
    ) -> list[UserNotificationPreferenceTable]:
        """Full replace: delete all (user_id, notification_type) rows then insert new ones."""
        del_stmt = delete(UserNotificationPreferenceTable).where(
            UserNotificationPreferenceTable.user_id == user_id,
            UserNotificationPreferenceTable.notification_type == notification_type,
        )
        await self.session.exec(del_stmt)

        created = []
        for entry in entries:
            entry.user_id = user_id
            entry.notification_type = notification_type
            self.session.add(entry)
            created.append(entry)

        await self.session.commit()
        for obj in created:
            await self.session.refresh(obj)
        return created

    async def ensure_defaults(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        recipient_email: Optional[str],
        recipient_phone: Optional[str],
        webhook_url: Optional[str],
    ) -> list[UserNotificationPreferenceTable]:
        """
        Lazy init: if user has no preferences for this notification_type, create them.

        Priority order:
        1. Explicit recipient data from the current request.
        2. Copy channels from the user's preferences for OTHER notification types —
           handles the case where a new notification_type is added to the registry
           after users have already configured their preferences.
        3. Return [] if the user has no preferences at all yet.

        Idempotent — does nothing if preferences for this type already exist.
        """
        existing = await self.get_by_user_and_type(user_id, notification_type)
        if existing:
            return list(existing)

        defaults = []

        # Phase 1: build from explicit request data — driven by channel.recipient_field
        address_map: dict[str, Optional[str]] = {
            "recipient_email": recipient_email,
            "recipient_phone": recipient_phone,
            "webhook_url": webhook_url,
        }
        for channel in NotificationChannel:
            field = channel.recipient_field
            if field is None:
                continue  # PLATFORM is opt-in, never auto-created here
            address = address_map.get(field)
            if address:
                defaults.append(
                    UserNotificationPreferenceTable(
                        user_id=user_id,
                        notification_type=notification_type,
                        channel=channel,
                        recipient_address=address,
                    )
                )

        # Phase 2: if request had no data, copy channels from the user's other preferences.
        # This handles new notification_types added after users are already onboarded —
        # their address is already stored under other types.
        if not defaults:
            all_user_prefs = await self.get_by_user(user_id)
            seen: set[NotificationChannel] = set()
            for pref in all_user_prefs:
                if pref.channel not in seen:
                    seen.add(pref.channel)
                    defaults.append(
                        UserNotificationPreferenceTable(
                            user_id=user_id,
                            notification_type=notification_type,
                            channel=pref.channel,
                            recipient_address=pref.recipient_address,
                        )
                    )

        if not defaults:
            return []

        try:
            for pref in defaults:
                self.session.add(pref)
            await self.session.commit()
            for pref in defaults:
                await self.session.refresh(pref)
            return defaults
        except IntegrityError:
            # Concurrent request already inserted preferences — roll back and return theirs.
            await self.session.rollback()
            existing = await self.get_by_user_and_type(user_id, notification_type)
            return list(existing)
