import pytest
from notification_registry import LocalNotificationClient
from notification_registry import NotificationChannel
from notification_registry import NotificationMessage
from notification_registry import NotificationMetadata
from notification_registry import NotificationPriority
from notification_registry import NotificationType

from notification_service.dispatcher import dispatch
from tests.utils.factories import ResetPasswordPayloadFactory
from tests.utils.factories import WebhookResetPasswordPayloadFactory


_ADDRESS = {
    NotificationChannel.EMAIL: "test@example.com",
    NotificationChannel.WEBHOOK: "https://hooks.example.com/notify",
    NotificationChannel.PLATFORM: None,
    NotificationChannel.WHATSAPP: "+79991234567",
}


def _make_message(
    channel: NotificationChannel, webhook: bool = False
) -> NotificationMessage:
    payload = (
        WebhookResetPasswordPayloadFactory.build()
        if webhook
        else ResetPasswordPayloadFactory.build()
    )
    return NotificationMessage(
        metadata=NotificationMetadata(
            notification_type=NotificationType.RESET_PASSWORD,
            channel=channel,
            priority=NotificationPriority.NORMAL,
            recipient_address=_ADDRESS[channel],
        ),
        payload=payload,
    )


class TestDispatch:
    def test_email_calls_client_publish(self):
        client = LocalNotificationClient()
        message = _make_message(NotificationChannel.EMAIL)

        with client:
            dispatch(message, client=client)

        assert len(client.published) == 1
        queue_name, _ = client.published[0]
        assert queue_name == NotificationChannel.EMAIL.queue_name

    def test_platform_calls_client_publish(self):
        client = LocalNotificationClient()
        message = _make_message(NotificationChannel.PLATFORM)

        with client:
            dispatch(message, client=client)

        assert len(client.published) == 1
        queue_name, _ = client.published[0]
        assert queue_name == NotificationChannel.PLATFORM.queue_name

    def test_webhook_calls_client_publish(self):
        client = LocalNotificationClient()
        message = _make_message(NotificationChannel.WEBHOOK, webhook=True)

        with client:
            dispatch(message, client=client)

        assert len(client.published) == 1
        queue_name, _ = client.published[0]
        assert queue_name == NotificationChannel.WEBHOOK.queue_name

    def test_whatsapp_raises_not_implemented(self):
        client = LocalNotificationClient()
        message = _make_message(NotificationChannel.WHATSAPP)

        with pytest.raises(NotImplementedError, match="WHATSAPP"):
            dispatch(message, client=client)
