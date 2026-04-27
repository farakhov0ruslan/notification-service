import asyncio

from notification_registry import LocalNotificationClient
from notification_registry import NotificationChannel
from notification_registry import NotificationMessage
from notification_registry import NotificationMetadata
from notification_registry import NotificationPriority
from notification_registry import NotificationType
from notification_registry import serialize_message
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from notification_service.infrastructure.enums import NotificationStatus
from notification_service.infrastructure.models import NotificationTable
from tests.utils.factories import ResetPasswordPayloadFactory
from tests.utils.factories import WebhookResetPasswordPayloadFactory


def _make_message(
    channel: NotificationChannel = NotificationChannel.EMAIL,
) -> NotificationMessage:
    payload = (
        WebhookResetPasswordPayloadFactory.build()
        if channel == NotificationChannel.WEBHOOK
        else ResetPasswordPayloadFactory.build()
    )
    return NotificationMessage(
        metadata=NotificationMetadata(
            notification_type=NotificationType.RESET_PASSWORD,
            channel=channel,
            priority=NotificationPriority.NORMAL,
        ),
        payload=payload,
    )


def _make_session_maker(engine):
    return async_sessionmaker(class_=AsyncSession, expire_on_commit=False, bind=engine)


def _create_notification(
    engine, message: NotificationMessage, status=NotificationStatus.PENDING
) -> None:
    notification = NotificationTable(
        id=message.metadata.notification_id,
        notification_type=message.metadata.notification_type,
        channel=message.metadata.channel,
        priority=message.metadata.priority,
        status=status,
    )

    async def _async():
        async with _make_session_maker(engine)() as s:
            s.add(notification)
            await s.commit()

    asyncio.run(_async())


def _get_notification(engine, notification_id) -> NotificationTable | None:
    async def _async():
        async with _make_session_maker(engine)() as s:
            result = await s.exec(
                select(NotificationTable).where(NotificationTable.id == notification_id)
            )
            return result.first()

    return asyncio.run(_async())


def _make_router_with_mocks(mocker):
    from notification_service.router.router import NotificationRouter

    mocker.patch("notification_service.router.router.RabbitMQNotificationClient")
    mocker.patch("notification_service.router.router.RabbitConsumer")
    mocker.patch("notification_service.router.router.ThreadedRabbitConsumer")
    mocker.patch("notification_service.router.router.RABBIT_MQ_CONFIG")
    mocker.patch("notification_service.router.router.threading.Thread")

    return NotificationRouter()


class TestNotificationRouter:
    def test_handle_message_email_routes_and_updates_status(self, mocker, engine):
        router = _make_router_with_mocks(mocker)
        message = _make_message(NotificationChannel.EMAIL)
        _create_notification(engine, message)

        client = LocalNotificationClient()
        router._client = client
        body = serialize_message(message)

        with client:
            asyncio.run(router._handle_message_async(body))

        assert len(client.published) == 1
        queue_name, _ = client.published[0]
        assert queue_name == NotificationChannel.EMAIL.queue_name

        notification = _get_notification(engine, message.metadata.notification_id)
        assert notification.status == NotificationStatus.SENT

    def test_handle_message_webhook_routes_and_updates_status(self, mocker, engine):
        router = _make_router_with_mocks(mocker)
        message = _make_message(NotificationChannel.WEBHOOK)
        _create_notification(engine, message)

        client = LocalNotificationClient()
        router._client = client
        body = serialize_message(message)

        with client:
            asyncio.run(router._handle_message_async(body))

        assert len(client.published) == 1
        queue_name, _ = client.published[0]
        assert queue_name == NotificationChannel.WEBHOOK.queue_name

        notification = _get_notification(engine, message.metadata.notification_id)
        assert notification.status == NotificationStatus.SENT

    def test_handle_message_skips_already_sent(self, mocker, engine):
        router = _make_router_with_mocks(mocker)
        message = _make_message(NotificationChannel.EMAIL)
        _create_notification(engine, message, status=NotificationStatus.SENT)

        client = LocalNotificationClient()
        router._client = client
        body = serialize_message(message)

        with client:
            asyncio.run(router._handle_message_async(body))

        assert len(client.published) == 0

    def test_handle_message_skips_if_not_found_in_db(self, mocker, engine):
        router = _make_router_with_mocks(mocker)
        message = _make_message(NotificationChannel.EMAIL)
        # intentionally not creating notification in DB

        client = LocalNotificationClient()
        router._client = client
        body = serialize_message(message)

        with client:
            asyncio.run(router._handle_message_async(body))

        assert len(client.published) == 0

    def test_run_starts_client_and_threaded_consumer(self, mocker):
        import notification_service.router.router as router_module

        router = _make_router_with_mocks(mocker)
        router.run()

        router._client.start.assert_called_once()
        router_module.ThreadedRabbitConsumer.return_value.start.assert_called_once()

    def test_stop_stops_consumer_and_closes_client(self, mocker):
        router = _make_router_with_mocks(mocker)

        router.stop()

        router._consumer.stop.assert_called_once()
        router._client.close.assert_called_once()
