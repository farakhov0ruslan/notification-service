from notification_registry import NotificationChannel
from notification_registry import NotificationClient
from notification_registry import NotificationMessage
from utils_library.Logging.log import get_logger

LOGGER = get_logger(__name__)


def dispatch(message: NotificationMessage, client: NotificationClient) -> None:
    channel = message.metadata.channel
    if channel == NotificationChannel.WHATSAPP:
        raise NotImplementedError("WHATSAPP handler not implemented yet")
    if channel not in NotificationChannel:
        raise NotImplementedError(f"Channel {channel!r} handler not implemented yet")

    LOGGER.info(
        f"Dispatching notification_id={message.metadata.notification_id} "
        f"→ {channel.queue_name!r}"
    )
    client.publish(message)
