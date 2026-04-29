from unittest.mock import MagicMock
from unittest.mock import patch

from notification_registry import LocalNotificationClient
from notification_registry import NotificationChannel
from notification_registry import NotificationMessage
from notification_registry import NotificationMetadata
from notification_registry import NotificationPriority
from notification_registry import NotificationType
from notification_registry import ResetPasswordPayload

from tests.utils.factories import ResetPasswordPayloadFactory


def patched_publisher() -> MagicMock:
    """Patch PriorityRabbitPublisher in server to a MagicMock usable as context manager."""
    publisher = MagicMock()
    publisher.__enter__ = MagicMock(return_value=publisher)
    publisher.__exit__ = MagicMock(return_value=False)
    patcher = patch(
        "notification_service.service.server.PriorityRabbitPublisher",
        return_value=publisher,
    )
    patcher.start()
    return publisher


def build_reset_password_message(
    payload: ResetPasswordPayload | None = None,
) -> NotificationMessage:
    p = payload or ResetPasswordPayloadFactory.build()
    return NotificationMessage(
        metadata=NotificationMetadata(
            notification_type=NotificationType.RESET_PASSWORD,
            channel=NotificationChannel.EMAIL,
            priority=NotificationPriority.NORMAL,
        ),
        payload=p,
    )


def local_client_for_router() -> LocalNotificationClient:
    return LocalNotificationClient()
