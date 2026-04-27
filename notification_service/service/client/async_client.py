from typing import Optional

from notification_registry import NotificationChannel
from notification_registry import NotificationPriority
from notification_registry import NotificationType
from utils_library.GrpcService.async_call import async_call_grpc

from notification_service.service.client import dto
from notification_service.service.client.dto import SendNotificationRequest
from notification_service.service.config import NOTIFICATION_SERVICE_CONFIG
from notification_service.service.proto import notification_service_pb2 as pb2
from notification_service.service.proto.notification_service_pb2_grpc import (
    NotificationServiceStub,
)


async def grpc_send_notification(
    request: SendNotificationRequest,
) -> dto.SendNotificationResult:
    nt = request.notification_type
    ch = request.channel
    pr = request.priority

    kwargs: dict = {
        "notification_type": nt.value if isinstance(nt, NotificationType) else nt,
        "payload_json": request.payload.model_dump_json(),
    }
    if ch is not None:
        kwargs["channel"] = ch.value if isinstance(ch, NotificationChannel) else ch
    if pr is not None:
        kwargs["priority"] = pr.value if isinstance(pr, NotificationPriority) else pr
    if request.recipient_id is not None:
        kwargs["recipient_id"] = request.recipient_id
    if request.recipient_address is not None:
        kwargs["recipient_address"] = request.recipient_address
    if request.scheduled_at is not None:
        kwargs["scheduled_at"] = request.scheduled_at

    response: pb2.SendNotificationResponse = await async_call_grpc(
        NotificationServiceStub,
        "SendNotification",
        pb2.SendNotificationRequest(**kwargs),
        config=NOTIFICATION_SERVICE_CONFIG,
    )

    return dto.SendNotificationResult(
        success=response.success,
        notification_id=response.notification_id,
        status=response.status,
        message=response.message,
        notification_ids=list(response.notification_ids),
    )


async def grpc_get_notification_status(
    notification_id: str,
) -> dto.NotificationStatusResult:
    response: pb2.GetNotificationStatusResponse = await async_call_grpc(
        NotificationServiceStub,
        "GetNotificationStatus",
        pb2.GetNotificationStatusRequest(notification_id=notification_id),
        config=NOTIFICATION_SERVICE_CONFIG,
    )

    return dto.NotificationStatusResult(
        success=response.success,
        notification_id=response.notification_id,
        status=response.status or None,
        channel=response.channel or None,
        notification_type=response.notification_type or None,
        last_error=response.last_error if response.HasField("last_error") else None,
        scheduled_at=response.scheduled_at
        if response.HasField("scheduled_at")
        else None,
        sent_at=response.sent_at if response.HasField("sent_at") else None,
        created_at=response.created_at or None,
    )


async def grpc_cancel_notification(
    notification_id: str,
) -> dto.CancelNotificationResult:
    response: pb2.CancelNotificationResponse = await async_call_grpc(
        NotificationServiceStub,
        "CancelNotification",
        pb2.CancelNotificationRequest(notification_id=notification_id),
        config=NOTIFICATION_SERVICE_CONFIG,
    )

    return dto.CancelNotificationResult(
        success=response.success,
        notification_id=response.notification_id,
        status=response.status,
        message=response.message,
    )


async def grpc_list_notifications(
    *,
    recipient_id: Optional[str] = None,
    status: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dto.ListNotificationsResult:
    kwargs: dict = {"limit": limit, "offset": offset}
    if recipient_id is not None:
        kwargs["recipient_id"] = recipient_id
    if status is not None:
        kwargs["status"] = status
    if channel is not None:
        kwargs["channel"] = channel

    response: pb2.ListNotificationsResponse = await async_call_grpc(
        NotificationServiceStub,
        "ListNotifications",
        pb2.ListNotificationsRequest(**kwargs),
        config=NOTIFICATION_SERVICE_CONFIG,
    )

    notifications = [
        dto.NotificationItem(
            notification_id=n.notification_id,
            notification_type=n.notification_type,
            channel=n.channel,
            priority=n.priority,
            status=n.status,
            recipient_id=n.recipient_id if n.HasField("recipient_id") else None,
            recipient_address=n.recipient_address
            if n.HasField("recipient_address")
            else None,
            last_error=n.last_error if n.HasField("last_error") else None,
            scheduled_at=n.scheduled_at if n.HasField("scheduled_at") else None,
            sent_at=n.sent_at if n.HasField("sent_at") else None,
            created_at=n.created_at,
        )
        for n in response.notifications
    ]

    return dto.ListNotificationsResult(
        success=response.success,
        notifications=notifications,
        total=response.total,
    )


async def grpc_get_user_preferences(
    user_id: str,
    notification_type: Optional[str] = None,
) -> dto.GetUserPreferencesResult:
    kwargs: dict = {"user_id": user_id}
    if notification_type is not None:
        kwargs["notification_type"] = notification_type

    response: pb2.GetUserPreferencesResponse = await async_call_grpc(
        NotificationServiceStub,
        "GetUserPreferences",
        pb2.GetUserPreferencesRequest(**kwargs),
        config=NOTIFICATION_SERVICE_CONFIG,
    )

    preferences = [
        dto.UserPreference(
            user_id=p.user_id,
            notification_type=p.notification_type,
            channel=p.channel,
            recipient_address=p.recipient_address
            if p.HasField("recipient_address")
            else None,
        )
        for p in response.preferences
    ]

    return dto.GetUserPreferencesResult(
        success=response.success,
        preferences=preferences,
    )


async def grpc_set_user_preferences(
    user_id: str,
    notification_type: str,
    preferences: list[dto.UserPreference],
) -> dto.SetUserPreferencesResult:
    items = [
        pb2.UserPreferenceItem(
            user_id=p.user_id,
            notification_type=p.notification_type,
            channel=p.channel,
            **(
                {"recipient_address": p.recipient_address}
                if p.recipient_address is not None
                else {}
            ),
        )
        for p in preferences
    ]

    response: pb2.SetUserPreferencesResponse = await async_call_grpc(
        NotificationServiceStub,
        "SetUserPreferences",
        pb2.SetUserPreferencesRequest(
            user_id=user_id,
            notification_type=notification_type,
            preferences=items,
        ),
        config=NOTIFICATION_SERVICE_CONFIG,
    )

    return dto.SetUserPreferencesResult(
        success=response.success,
        message=response.message,
    )


if __name__ == "__main__":
    import asyncio
    from datetime import UTC
    from datetime import datetime
    from datetime import timedelta
    from uuid import uuid4

    from notification_registry import ResetPasswordPayload
    from utils_library.Logging.log import configure_logger
    from utils_library.Logging.log import get_logger

    configure_logger(__name__, "debug")
    LOGGER = get_logger(__name__)

    _SMOKE_CHANNELS: list[tuple[NotificationChannel, str]] = [
        (NotificationChannel.EMAIL, "farakhov0ruslan@gmail.com"),
        (
            NotificationChannel.WEBHOOK,
            "https://webhook.site/36306d30-36d9-43ea-8f84-5d5022ecce22",
        ),
    ]

    async def _send_for_channel(
        channel: NotificationChannel,
        recipient_address: str,
    ) -> str | None:
        payload = ResetPasswordPayload(
            user_id=uuid4(),
            reset_url="https://example.com/reset?token=test123",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            user_name="Test User",
            user_ip="127.0.0.1",
            user_agent="Mozilla/5.0 (smoke-test)",
            recipient_email=recipient_address
            if channel == NotificationChannel.EMAIL
            else None,
            webhook_url=recipient_address
            if channel == NotificationChannel.WEBHOOK
            else None,
        )
        result = await grpc_send_notification(
            SendNotificationRequest(
                notification_type=NotificationType.RESET_PASSWORD,
                channel=channel,
                payload=payload,
                recipient_address=recipient_address,
            )
        )
        LOGGER.info(
            f"  [{channel.value}] success={result.success}, "
            f"id={result.notification_id}, status={result.status}, "
            f"message={result.message!r}"
        )
        return result.notification_id if result.success else None

    async def main():
        LOGGER.info("=" * 60)
        LOGGER.info("notification-service smoke test")
        LOGGER.info("=" * 60)

        # ── 1. SendNotification for each channel ──────────────────
        LOGGER.info(
            f"[1] SendNotification → channels: {[c.value for c, _ in _SMOKE_CHANNELS]}"
        )
        sent_ids: dict[NotificationChannel, str] = {}
        for channel, addr in _SMOKE_CHANNELS:
            nid = await _send_for_channel(channel, addr)
            if nid:
                sent_ids[channel] = nid

        if not sent_ids:
            LOGGER.error("All SendNotification calls FAILED — aborting")
            return

        # ── 2. GetNotificationStatus immediately ──────────────────
        LOGGER.info("[2] GetNotificationStatus (immediate)")
        for channel, nid in sent_ids.items():
            status = await grpc_get_notification_status(nid)
            LOGGER.info(
                f"  [{channel.value}] id={nid}, status={status.status}, "
                f"channel={status.channel}"
            )

        # ── 3. Wait for Router, then check again ──────────────────
        LOGGER.info("[3] Waiting 2s for Router to route messages...")
        await asyncio.sleep(2)
        for channel, nid in sent_ids.items():
            status = await grpc_get_notification_status(nid)
            LOGGER.info(
                f"  [{channel.value}] status after 2s: {status.status} "
                f"(expect 'sent' if Router + handler are running)"
            )

        # ── 4. ListNotifications ──────────────────────────────────
        LOGGER.info("[4] ListNotifications (limit=10)")
        list_result = await grpc_list_notifications(limit=10)
        LOGGER.info(f"  total={list_result.total}")
        for item in list_result.notifications[:5]:
            LOGGER.info(
                f"    id={item.notification_id}, channel={item.channel}, status={item.status}"
            )

        LOGGER.info("=" * 60)

    asyncio.run(main())
