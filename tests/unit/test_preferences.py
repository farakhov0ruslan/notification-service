import asyncio
from uuid import uuid4

from notification_registry import NotificationChannel
from notification_registry import NotificationType
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from notification_service.infrastructure.crud.crud_user_preference import CRUDUserPreference
from notification_service.infrastructure.models import UserNotificationPreferenceTable


def _run_ensure_defaults(engine, *, user_id, notification_type, recipient_address=None):
    async def _async():
        sm = async_sessionmaker(class_=AsyncSession, expire_on_commit=False, bind=engine)
        async with sm() as s:
            crud = CRUDUserPreference(UserNotificationPreferenceTable, s)
            return await crud.ensure_defaults(
                user_id=user_id,
                notification_type=notification_type,
                recipient_address=recipient_address,
            )

    return asyncio.run(_async())


class TestEnsureDefaultsIncludesPlatform:
    def test_platform_created_even_with_no_address_and_no_other_prefs(self, engine):
        user_id = uuid4()

        result = _run_ensure_defaults(
            engine,
            user_id=user_id,
            notification_type=NotificationType.RESET_PASSWORD,
            recipient_address=None,
        )

        channels = [r.channel for r in result]
        assert NotificationChannel.PLATFORM in channels

    def test_platform_created_alongside_other_channels_when_address_provided(self, engine):
        user_id = uuid4()

        result = _run_ensure_defaults(
            engine,
            user_id=user_id,
            notification_type=NotificationType.RESET_PASSWORD,
            recipient_address="user@example.com",
        )

        channels = [r.channel for r in result]
        assert NotificationChannel.PLATFORM in channels
        assert NotificationChannel.EMAIL in channels

    def test_platform_recipient_address_is_user_id(self, engine):
        user_id = uuid4()

        result = _run_ensure_defaults(
            engine,
            user_id=user_id,
            notification_type=NotificationType.ANALYTICS,
            recipient_address=None,
        )

        platform_pref = next(
            (r for r in result if r.channel == NotificationChannel.PLATFORM), None
        )
        assert platform_pref is not None
        assert platform_pref.recipient_address == str(user_id)

    def test_platform_not_duplicated_on_second_call(self, engine):
        user_id = uuid4()

        first = _run_ensure_defaults(
            engine,
            user_id=user_id,
            notification_type=NotificationType.RESET_PASSWORD,
        )
        second = _run_ensure_defaults(
            engine,
            user_id=user_id,
            notification_type=NotificationType.RESET_PASSWORD,
        )

        platform_rows = [r for r in second if r.channel == NotificationChannel.PLATFORM]
        assert len(platform_rows) == 1
