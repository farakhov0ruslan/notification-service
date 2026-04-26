import asyncio
from unittest.mock import MagicMock
from uuid import UUID
from uuid import uuid4

from notification_registry import NotificationChannel
from notification_registry import NotificationPriority
from notification_registry import NotificationType
from notification_registry import deserialize_message
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from notification_service.infrastructure.enums import NotificationStatus
from notification_service.infrastructure.models import NotificationTable
from notification_service.service.proto import notification_service_pb2 as pb2
from tests.utils.mocks import patched_publisher


def _build_request(payload, notification_type="reset_password", channel="email"):
    request = MagicMock()
    request.notification_type = notification_type
    request.channel = channel
    request.HasField = lambda field: field not in (
        "priority", "recipient_id", "scheduled_at", "subject",
        "recipient_phone", "webhook_url",
    )
    request.recipient_email = payload.recipient_email
    request.payload_json = payload.model_dump_json()
    return request

# TODO: надо использовать патченный ioc
def _get_notification(engine, notification_id_str: str) -> NotificationTable | None:
    async def _async():
        sm = async_sessionmaker(class_=AsyncSession, expire_on_commit=False, bind=engine)
        async with sm() as s:
            result = await s.exec(
                select(NotificationTable).where(
                    NotificationTable.id == UUID(notification_id_str)
                )
            )
            return result.first()

    return asyncio.run(_async())


class TestSendNotification:
    def test_success_persists_notification_to_db(self, engine, reset_password_payload, mocker):
        from notification_service.service.server import NotificationServiceServicer

        patched_publisher(mocker)
        servicer = NotificationServiceServicer()
        response = servicer.SendNotification(_build_request(reset_password_payload), MagicMock())

        assert response.success is True
        assert response.status == NotificationStatus.PENDING.value

        notification = _get_notification(engine, response.notification_id)
        assert notification is not None
        assert notification.status == NotificationStatus.PENDING
        assert notification.channel == NotificationChannel.EMAIL
        assert notification.notification_type == NotificationType.RESET_PASSWORD
        assert notification.recipient_email == reset_password_payload.recipient_email

    def test_success_publishes_valid_notification_message(self, engine, reset_password_payload, mocker):
        from notification_service.service.server import NotificationServiceServicer

        publisher = patched_publisher(mocker)
        servicer = NotificationServiceServicer()
        response = servicer.SendNotification(_build_request(reset_password_payload), MagicMock())

        assert response.success is True
        publisher.publish.assert_called_once()
        body_str = publisher.publish.call_args.kwargs["message"]
        msg = deserialize_message(body_str.encode("utf-8"))
        assert msg.metadata.channel == NotificationChannel.EMAIL
        assert msg.metadata.notification_type == NotificationType.RESET_PASSWORD
        assert msg.payload.recipient_email == reset_password_payload.recipient_email

    def test_notification_id_in_response_matches_db_record(self, engine, reset_password_payload, mocker):
        from notification_service.service.server import NotificationServiceServicer

        patched_publisher(mocker)
        servicer = NotificationServiceServicer()
        response = servicer.SendNotification(_build_request(reset_password_payload), MagicMock())

        assert response.success is True
        notification = _get_notification(engine, response.notification_id)
        assert notification is not None
        assert str(notification.id) == response.notification_id

    def test_unknown_notification_type_returns_failure(self, reset_password_payload, mocker):
        from notification_service.service.server import NotificationServiceServicer

        patched_publisher(mocker)
        servicer = NotificationServiceServicer()
        request = _build_request(reset_password_payload, notification_type="NONEXISTENT_TYPE")
        response = servicer.SendNotification(request, MagicMock())

        assert response.success is False
        assert "NONEXISTENT_TYPE" in response.message

    def test_invalid_payload_json_returns_failure(self, reset_password_payload, mocker):
        from notification_service.service.server import NotificationServiceServicer

        patched_publisher(mocker)
        servicer = NotificationServiceServicer()
        request = _build_request(reset_password_payload)
        request.payload_json = "not-valid-json"
        response = servicer.SendNotification(request, MagicMock())

        assert response.success is False


def _insert_notifications(engine, notifications: list[NotificationTable]) -> None:
    async def _async():
        sm = async_sessionmaker(class_=AsyncSession, expire_on_commit=False, bind=engine)
        async with sm() as s:
            for notification in notifications:
                s.add(notification)
            await s.commit()

    asyncio.run(_async())


def _make_notification(
    *,
    recipient_id=None,
    channel=NotificationChannel.EMAIL,
    status=NotificationStatus.PENDING,
) -> NotificationTable:
    return NotificationTable(
        id=uuid4(),
        recipient_id=recipient_id,
        notification_type=NotificationType.RESET_PASSWORD,
        channel=channel,
        priority=NotificationPriority.NORMAL,
        status=status,
    )


class TestListNotifications:
    def test_filters_by_channel_and_status(self, engine, mocker):
        from notification_service.service.server import NotificationServiceServicer

        patched_publisher(mocker)
        servicer = NotificationServiceServicer()
        recipient_id = uuid4()
        _insert_notifications(
            engine,
            [
                _make_notification(
                    recipient_id=recipient_id,
                    channel=NotificationChannel.EMAIL,
                    status=NotificationStatus.PENDING,
                ),
                _make_notification(
                    recipient_id=recipient_id,
                    channel=NotificationChannel.WEBHOOK,
                    status=NotificationStatus.PENDING,
                ),
                _make_notification(
                    recipient_id=recipient_id,
                    channel=NotificationChannel.WEBHOOK,
                    status=NotificationStatus.SENT,
                ),
            ],
        )

        response = servicer.ListNotifications(
            pb2.ListNotificationsRequest(
                recipient_id=str(recipient_id),
                channel=NotificationChannel.WEBHOOK.value,
                status=NotificationStatus.PENDING.value,
                limit=20,
            ),
            MagicMock(),
        )

        assert response.success is True
        assert response.total == 1
        assert len(response.notifications) == 1
        assert response.notifications[0].channel == NotificationChannel.WEBHOOK.value
        assert response.notifications[0].status == NotificationStatus.PENDING.value

    def test_uses_offset_for_pagination(self, engine, mocker):
        from notification_service.service.server import NotificationServiceServicer

        patched_publisher(mocker)
        servicer = NotificationServiceServicer()
        recipient_id = uuid4()
        _insert_notifications(
            engine,
            [
                _make_notification(recipient_id=recipient_id),
                _make_notification(recipient_id=recipient_id),
                _make_notification(recipient_id=recipient_id),
            ],
        )

        first_page = servicer.ListNotifications(
            pb2.ListNotificationsRequest(
                recipient_id=str(recipient_id),
                limit=1,
                offset=0,
            ),
            MagicMock(),
        )
        second_page = servicer.ListNotifications(
            pb2.ListNotificationsRequest(
                recipient_id=str(recipient_id),
                limit=1,
                offset=1,
            ),
            MagicMock(),
        )

        assert first_page.success is True
        assert second_page.success is True
        assert first_page.total == 3
        assert second_page.total == 3
        assert first_page.notifications[0].notification_id != second_page.notifications[0].notification_id
