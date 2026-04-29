"""Integration test: dispatcher routes messages to channel queues via LocalNotificationClient."""

from notification_registry import AnalyticsPayload
from notification_registry import LocalNotificationClient
from notification_registry import NotificationChannel
from notification_registry import NotificationMessage
from notification_registry import NotificationMetadata
from notification_registry import NotificationPriority
from notification_registry import NotificationType
from notification_registry import ResetPasswordPayload
from notification_registry import deserialize_message

from notification_service.dispatcher import dispatch
from tests.utils.factories import WEBHOOK_URL
from tests.utils.factories import ResetPasswordPayloadFactory
from tests.utils.factories import WebhookAnalyticsPayloadFactory
from tests.utils.factories import WebhookResetPasswordPayloadFactory


TEST_EMAIL = "test@example.com"
TEST_WEBHOOK = WEBHOOK_URL


def _build_email_message(payload=None) -> NotificationMessage:
    p = payload or ResetPasswordPayloadFactory.build()
    return NotificationMessage(
        metadata=NotificationMetadata(
            notification_type=NotificationType.RESET_PASSWORD,
            channel=NotificationChannel.EMAIL,
            priority=NotificationPriority.NORMAL,
            recipient_address=TEST_EMAIL,
        ),
        payload=p,
    )


def _build_webhook_message(
    payload: ResetPasswordPayload | AnalyticsPayload | None = None,
    notification_type: NotificationType = NotificationType.RESET_PASSWORD,
) -> NotificationMessage:
    p = payload or WebhookResetPasswordPayloadFactory.build()
    return NotificationMessage(
        metadata=NotificationMetadata(
            notification_type=notification_type,
            channel=NotificationChannel.WEBHOOK,
            priority=NotificationPriority.NORMAL,
            recipient_address=TEST_WEBHOOK,
        ),
        payload=p,
    )


class TestLocalPipeline:
    def test_email_message_published_to_email_queue(self, reset_password_payload):
        message = _build_email_message(reset_password_payload)
        client = LocalNotificationClient()

        with client:
            dispatch(message, client=client)

        assert len(client.published) == 1
        queue_name, body = client.published[0]
        assert queue_name == NotificationChannel.EMAIL.queue_name

    def test_published_body_is_valid_notification_message(self, reset_password_payload):
        message = _build_email_message(reset_password_payload)
        client = LocalNotificationClient()

        with client:
            dispatch(message, client=client)

        _, body = client.published[0]
        deserialized = deserialize_message(body)
        assert (
            deserialized.metadata.notification_type == NotificationType.RESET_PASSWORD
        )
        assert deserialized.metadata.channel == NotificationChannel.EMAIL
        assert deserialized.metadata.recipient_address == TEST_EMAIL

    def test_multiple_messages_stored_in_published(self, reset_password_payload):
        client = LocalNotificationClient()
        message = _build_email_message(reset_password_payload)

        with client:
            dispatch(message, client=client)
            dispatch(message, client=client)

        assert len(client.published) == 2

    def test_in_process_handler_invoked(self, reset_password_payload):
        received = []

        def handler(queue_name: str, body: bytes) -> None:
            received.append((queue_name, body))

        client = LocalNotificationClient(handler=handler)
        message = _build_email_message(reset_password_payload)

        with client:
            dispatch(message, client=client)

        assert len(received) == 1
        queue_name, body = received[0]
        assert queue_name == NotificationChannel.EMAIL.queue_name
        msg = deserialize_message(body)
        assert msg.metadata.notification_id == message.metadata.notification_id


class TestWebhookLocalPipeline:
    def test_webhook_message_published_to_webhook_queue(self):
        message = _build_webhook_message()
        client = LocalNotificationClient()

        with client:
            dispatch(message, client=client)

        assert len(client.published) == 1
        queue_name, _ = client.published[0]
        assert queue_name == NotificationChannel.WEBHOOK.queue_name

    def test_published_body_preserves_recipient_address(self):
        payload = WebhookResetPasswordPayloadFactory.build()
        message = _build_webhook_message(payload)
        client = LocalNotificationClient()

        with client:
            dispatch(message, client=client)

        _, body = client.published[0]
        deserialized = deserialize_message(body)
        assert deserialized.metadata.recipient_address == TEST_WEBHOOK

    def test_published_body_preserves_notification_type(self):
        message = _build_webhook_message()
        client = LocalNotificationClient()

        with client:
            dispatch(message, client=client)

        _, body = client.published[0]
        deserialized = deserialize_message(body)
        assert (
            deserialized.metadata.notification_type == NotificationType.RESET_PASSWORD
        )
        assert deserialized.metadata.channel == NotificationChannel.WEBHOOK

    def test_analytics_payload_published_to_webhook_queue(self):
        payload = WebhookAnalyticsPayloadFactory.build()
        message = _build_webhook_message(
            payload, notification_type=NotificationType.ANALYTICS
        )
        client = LocalNotificationClient()

        with client:
            dispatch(message, client=client)

        queue_name, _ = client.published[0]
        assert queue_name == NotificationChannel.WEBHOOK.queue_name

    def test_notification_id_preserved_in_published_body(self):
        message = _build_webhook_message()
        client = LocalNotificationClient()

        with client:
            dispatch(message, client=client)

        _, body = client.published[0]
        deserialized = deserialize_message(body)
        assert deserialized.metadata.notification_id == message.metadata.notification_id

    def test_in_process_handler_receives_webhook_message(self):
        received = []

        def handler(queue_name: str, body: bytes) -> None:
            received.append((queue_name, body))

        message = _build_webhook_message()
        client = LocalNotificationClient(handler=handler)

        with client:
            dispatch(message, client=client)

        assert len(received) == 1
        assert received[0][0] == NotificationChannel.WEBHOOK.queue_name
