import asyncio
import signal
import threading
from concurrent import futures
from datetime import datetime
from typing import Optional
from uuid import UUID

import dishka
import fire
import grpc
from notification_registry import PAYLOAD_TYPE_MAPPING
from notification_registry import NotificationChannel
from notification_registry import NotificationMessage
from notification_registry import NotificationMetadata
from notification_registry import NotificationPriority
from notification_registry import NotificationType
from notification_registry import serialize_message
from prometheus_client import start_http_server
from pydantic import AnyUrl
from pydantic import EmailStr
from pydantic import TypeAdapter
from utils_library.Logging.log import configure_logger
from utils_library.Logging.log import get_logger
from utils_library.RabbitMQ.publisher import RabbitPublisher
from utils_library.RabbitMQ.rabbitmq import RABBIT_MQ_CONFIG

from notification_service.infrastructure.enums import NotificationStatus
from notification_service.infrastructure.models import NotificationTable
from notification_service.infrastructure.models import UserNotificationPreferenceTable
from notification_service.ioc import IOC_CONTAINER
from notification_service.ioc import NotificationRepository
from notification_service.router.config import NOTIFICATION_ROUTER_CONFIG
from notification_service.service.config import NOTIFICATION_SERVICE_CONFIG
from notification_service.service.proto import notification_service_pb2 as pb2
from notification_service.service.proto import notification_service_pb2_grpc as pb2_grpc

LOGGER = get_logger(__name__)


def _dt_to_str(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.isoformat()


def _notification_to_item(n: NotificationTable) -> pb2.NotificationItem:
    return pb2.NotificationItem(
        notification_id=str(n.id),
        notification_type=n.notification_type,
        channel=n.channel,
        priority=n.priority.value,
        status=n.status.value,
        recipient_id=str(n.recipient_id) if n.recipient_id else None,
        recipient_address=n.recipient_address,
        last_error=n.last_error,
        scheduled_at=_dt_to_str(n.scheduled_at),
        sent_at=_dt_to_str(n.sent_at),
        created_at=_dt_to_str(n.created_at) if hasattr(n, "created_at") else "",
    )


def _pref_to_item(p: UserNotificationPreferenceTable) -> pb2.UserPreferenceItem:
    return pb2.UserPreferenceItem(
        user_id=str(p.user_id),
        notification_type=p.notification_type,
        channel=p.channel,
        recipient_address=p.recipient_address or "",
    )


class NotificationServiceServicer(pb2_grpc.NotificationServiceServicer):
    def __init__(self):
        # Single persistent event loop running in a background daemon thread.
        # All async DB operations are submitted here via run_coroutine_threadsafe.
        # This avoids the "Future attached to a different loop" error that occurs
        # when asyncio.run() is called multiple times: asyncpg binds connections
        # to the loop they were created in, so every call must share one loop.
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(
            target=self._loop.run_forever, daemon=True, name="grpc-async-loop"
        )
        self._loop_thread.start()
        self._publisher = RabbitPublisher(rabbit_config=RABBIT_MQ_CONFIG)
        self._publisher.__enter__()
        self._closed = False

    def _run(self, coro):
        """Submit a coroutine to the persistent loop and block until done."""
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._publisher.__exit__(None, None, None)
        self._loop.call_soon_threadsafe(self._loop.stop)

    # ─── SendNotification ────────────────────────────────────────────

    def SendNotification(self, request, context):
        LOGGER.debug(
            f"SendNotification request: type={request.notification_type!r}, "
            f"channel={request.channel if request.HasField('channel') else 'from_preferences'!r}, "
            f"recipient_id={request.recipient_id if request.HasField('recipient_id') else None!r}"
        )
        try:
            notification_type = NotificationType(request.notification_type)
            priority = (
                NotificationPriority(request.priority)
                if request.HasField("priority")
                else NotificationPriority.NORMAL
            )

            payload_cls = PAYLOAD_TYPE_MAPPING[notification_type]
            base_payload = payload_cls.model_validate_json(request.payload_json)
            LOGGER.debug(f"Payload validated: type={notification_type.value}")

            # Resolve dispatch list: [(channel, enriched_payload), ...]
            if request.HasField("channel") and request.channel:
                channel = NotificationChannel(request.channel)
                enriched = self._run(
                    self._enrich_payload_for_channel(base_payload, channel, request)
                )
                if enriched is None:
                    required = channel.recipient_field or ""
                    return pb2.SendNotificationResponse(
                        success=False,
                        message=(
                            f"Required field '{required}' for channel '{channel.value}' "
                            f"not found in request or user preferences"
                        ),
                    )
                dispatch_list = [(channel, enriched)]

            elif request.HasField("recipient_id") and request.recipient_id:
                dispatch_list = self._run(
                    self._resolve_from_preferences(
                        base_payload, request, notification_type
                    )
                )
                if not dispatch_list:
                    return pb2.SendNotificationResponse(
                        success=False,
                        message="No notification preferences found for user. "
                        "Set preferences first or provide an explicit channel.",
                    )
            else:
                return pb2.SendNotificationResponse(
                    success=False,
                    message="'channel' is required when 'recipient_id' is not provided",
                )

            notification_ids = []
            for ch, enriched_payload in dispatch_list:
                message = NotificationMessage(
                    metadata=NotificationMetadata(
                        notification_type=notification_type,
                        channel=ch,
                        priority=priority,
                    ),
                    payload=enriched_payload,
                )

                LOGGER.debug(
                    f"Persisting notification id={message.metadata.notification_id} to DB"
                )
                created = self._run(self._create_notification(message, request))
                LOGGER.info(
                    f"Notification persisted: id={created.id}, "
                    f"type={notification_type.value}, channel={ch.value}, status=PENDING"
                )

                body = serialize_message(message)
                LOGGER.debug(
                    f"Publishing notification id={created.id} "
                    f"to queue={NOTIFICATION_ROUTER_CONFIG.input_queue!r}"
                )
                self._publisher.publish(
                    message=body.decode("utf-8"),
                    queue=NOTIFICATION_ROUTER_CONFIG.input_queue,
                    declare_queue=True,
                )
                LOGGER.info(
                    f"Notification id={created.id} queued in {NOTIFICATION_ROUTER_CONFIG.input_queue!r}"
                )
                notification_ids.append(str(created.id))

            return pb2.SendNotificationResponse(
                success=True,
                notification_id=notification_ids[0],
                notification_ids=notification_ids,
                status=NotificationStatus.PENDING.value,
                message=f"Created {len(notification_ids)} notification(s)",
            )
        except (ValueError, KeyError) as e:
            LOGGER.warning(f"SendNotification validation error: {e}")
            return pb2.SendNotificationResponse(success=False, message=str(e))
        except Exception as e:
            LOGGER.exception("SendNotification failed", exc_info=e)
            return pb2.SendNotificationResponse(success=False, message=str(e))

    async def _enrich_payload_for_channel(
        self,
        payload,
        channel: NotificationChannel,
        request,
    ):
        """
        Enrich payload with recipient data needed by the given channel.
        Priority: explicit request field → user preferences.
        Returns None if the required field is missing from both sources.
        """
        field = channel.recipient_field
        if field is None:
            # PLATFORM: user_id already embedded in payload; no enrichment needed.
            return payload

        user_id: Optional[UUID] = None
        if request.HasField("recipient_id") and request.recipient_id:
            user_id = UUID(request.recipient_id)

        pref: Optional[UserNotificationPreferenceTable] = None
        if user_id is not None:
            async with IOC_CONTAINER(scope=dishka.Scope.REQUEST) as ioc:
                repo = await ioc.get(NotificationRepository)
                pref = await repo.user_preferences.get_by_user_and_channel(
                    user_id, channel
                )

        address = (
            (request.HasField("recipient_address") and request.recipient_address)
            or None
            if hasattr(request, "HasField")
            else getattr(request, "recipient_address", None)
        ) or (pref.recipient_address if pref else None)

        if not address:
            return None
        return payload.model_copy(update={field: address})

    async def _resolve_from_preferences(
        self,
        base_payload,
        request,
        notification_type: NotificationType,
    ) -> list[tuple[NotificationChannel, object]]:
        """
        Resolve dispatch list from user preferences, running lazy init on first call.
        Returns list of (channel, enriched_payload) tuples.
        """
        user_id = UUID(request.recipient_id)
        recipient_address = (
            request.recipient_address if request.HasField("recipient_address") else None
        )

        async with IOC_CONTAINER(scope=dishka.Scope.REQUEST) as ioc:
            repo = await ioc.get(NotificationRepository)
            prefs = await repo.user_preferences.ensure_defaults(
                user_id=user_id,
                notification_type=notification_type,
                recipient_address=recipient_address,
            )
            if not prefs:
                prefs = list(
                    await repo.user_preferences.get_by_user_and_type(
                        user_id, notification_type
                    )
                )

        result = []
        for pref in prefs:
            ch = NotificationChannel(pref.channel)
            field = ch.recipient_field
            if field is None:
                # PLATFORM: user_id already in payload; no enrichment needed.
                result.append((ch, base_payload))
                continue
            if pref.recipient_address:
                enriched = base_payload.model_copy(
                    update={field: pref.recipient_address}
                )
                result.append((ch, enriched))

        return result

    async def _create_notification(
        self, message: NotificationMessage, request
    ) -> NotificationTable:
        scheduled_at = None
        if request.HasField("scheduled_at") and request.scheduled_at:
            scheduled_at = datetime.fromisoformat(request.scheduled_at)

        recipient_id = None
        if request.HasField("recipient_id") and request.recipient_id:
            recipient_id = UUID(request.recipient_id)

        field = message.metadata.channel.recipient_field
        recipient_address = (
            str(getattr(message.payload, field))
            if field is not None and getattr(message.payload, field, None) is not None
            else None
        )

        notification = NotificationTable(
            id=message.metadata.notification_id,
            recipient_id=recipient_id,
            recipient_address=recipient_address,
            notification_type=message.metadata.notification_type.value,
            channel=message.metadata.channel.value,
            priority=message.metadata.priority,
            status=NotificationStatus.PENDING,
            scheduled_at=scheduled_at,
        )

        async with IOC_CONTAINER(scope=dishka.Scope.REQUEST) as ioc:
            repo = await ioc.get(NotificationRepository)
            created = await repo.notifications.create(obj_in=notification)
            await repo.notifications.session.commit()
            return created

    # ─── GetNotificationStatus ──────────────────────────────────────

    def GetNotificationStatus(self, request, context):
        LOGGER.debug(f"GetNotificationStatus: id={request.notification_id!r}")
        try:
            return self._run(self._get_notification_status(request))
        except Exception as e:
            LOGGER.exception("GetNotificationStatus failed", exc_info=e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return pb2.GetNotificationStatusResponse(success=False)

    async def _get_notification_status(self, request):
        async with IOC_CONTAINER(scope=dishka.Scope.REQUEST) as ioc:
            repo = await ioc.get(NotificationRepository)
            notification_id = UUID(request.notification_id)
            notification = await repo.notifications.get(id=notification_id)

            if notification is None:
                LOGGER.warning(f"GetNotificationStatus: id={notification_id} not found")
                return pb2.GetNotificationStatusResponse(
                    success=False,
                    notification_id=request.notification_id,
                    status="",
                    channel="",
                    notification_type="",
                    created_at="",
                )

            LOGGER.debug(
                f"GetNotificationStatus: id={notification_id}, status={notification.status.value}"
            )
            return pb2.GetNotificationStatusResponse(
                success=True,
                notification_id=str(notification.id),
                status=notification.status.value,
                channel=notification.channel,
                notification_type=notification.notification_type,
                last_error=notification.last_error,
                scheduled_at=_dt_to_str(notification.scheduled_at),
                sent_at=_dt_to_str(notification.sent_at),
                created_at=_dt_to_str(notification.created_at)
                if hasattr(notification, "created_at")
                else "",
            )

    # ─── CancelNotification ───────────────────────────────────────

    def CancelNotification(self, request, context):
        LOGGER.debug(f"CancelNotification: id={request.notification_id!r}")
        try:
            return self._run(self._cancel_notification(request))
        except Exception as e:
            LOGGER.exception("CancelNotification failed", exc_info=e)
            return pb2.CancelNotificationResponse(
                success=False,
                notification_id=request.notification_id,
                status="",
                message=str(e),
            )

    async def _cancel_notification(self, request):
        async with IOC_CONTAINER(scope=dishka.Scope.REQUEST) as ioc:
            repo = await ioc.get(NotificationRepository)
            notification_id = UUID(request.notification_id)
            notification = await repo.notifications.get(id=notification_id)

            if notification is None:
                LOGGER.warning(f"CancelNotification: id={notification_id} not found")
                return pb2.CancelNotificationResponse(
                    success=False,
                    notification_id=request.notification_id,
                    status="",
                    message="Notification not found",
                )

            if notification.status in NotificationStatus.finished_status():
                LOGGER.warning(
                    f"CancelNotification: id={notification_id} "
                    f"already in terminal status={notification.status.value}"
                )
                return pb2.CancelNotificationResponse(
                    success=False,
                    notification_id=request.notification_id,
                    status=notification.status.value,
                    message=f"Cannot cancel notification in status {notification.status.value}",
                )

            updated = await repo.notifications.update_status(
                notification_id, NotificationStatus.CANCELLED
            )
            LOGGER.info(f"Notification id={notification_id} cancelled")

            return pb2.CancelNotificationResponse(
                success=True,
                notification_id=str(updated.id),
                status=updated.status.value,
                message="Notification cancelled",
            )

    # ─── ListNotifications ────────────────────────────────────────

    def ListNotifications(self, request, context):
        LOGGER.debug(
            f"ListNotifications: limit={request.limit}, "
            f"recipient_id={getattr(request, 'recipient_id', None)!r}, "
            f"status={getattr(request, 'status', None)!r}"
        )
        try:
            return self._run(self._list_notifications(request))
        except Exception as e:
            LOGGER.exception("ListNotifications failed", exc_info=e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return pb2.ListNotificationsResponse(success=False, total=0)

    async def _list_notifications(self, request):
        async with IOC_CONTAINER(scope=dishka.Scope.REQUEST) as ioc:
            repo = await ioc.get(NotificationRepository)
            limit = request.limit if request.limit > 0 else 100
            offset = request.offset if request.offset > 0 else 0
            recipient_id = (
                UUID(request.recipient_id)
                if request.HasField("recipient_id") and request.recipient_id
                else None
            )
            status = (
                NotificationStatus(request.status)
                if request.HasField("status") and request.status
                else None
            )
            channel = (
                NotificationChannel(request.channel)
                if request.HasField("channel") and request.channel
                else None
            )
            LOGGER.debug(
                f"ListNotifications filters: recipient_id={recipient_id}, "
                f"status={status}, channel={channel}, limit={limit}, offset={offset}"
            )
            notifications = await repo.notifications.list_notifications(
                recipient_id=recipient_id,
                status=status,
                channel=channel,
                limit=limit,
                offset=offset,
            )
            total = await repo.notifications.count_notifications(
                recipient_id=recipient_id,
                status=status,
                channel=channel,
            )

            items = [_notification_to_item(n) for n in notifications]
            LOGGER.debug(f"ListNotifications: returning {len(items)} of {total} items")

            return pb2.ListNotificationsResponse(
                success=True,
                notifications=items,
                total=total,
            )

    # ─── GetUserPreferences ──────────────────────────────────────

    def GetUserPreferences(self, request, context):
        LOGGER.debug(
            f"GetUserPreferences: user_id={request.user_id!r}, "
            f"notification_type={request.notification_type if request.HasField('notification_type') else 'all'!r}"
        )
        try:
            return self._run(self._get_user_preferences(request))
        except Exception as e:
            LOGGER.exception("GetUserPreferences failed", exc_info=e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return pb2.GetUserPreferencesResponse(success=False)

    async def _get_user_preferences(self, request):
        user_id = UUID(request.user_id)
        async with IOC_CONTAINER(scope=dishka.Scope.REQUEST) as ioc:
            repo = await ioc.get(NotificationRepository)
            if request.HasField("notification_type") and request.notification_type:
                nt = NotificationType(request.notification_type)
                prefs = await repo.user_preferences.get_by_user_and_type(user_id, nt)
            else:
                prefs = await repo.user_preferences.get_by_user(user_id)

        return pb2.GetUserPreferencesResponse(
            success=True,
            preferences=[_pref_to_item(p) for p in prefs],
        )

    # ─── SetUserPreferences ──────────────────────────────────────

    def SetUserPreferences(self, request, context):
        LOGGER.debug(
            f"SetUserPreferences: user_id={request.user_id!r}, "
            f"notification_type={request.notification_type!r}, "
            f"count={len(request.preferences)}"
        )
        try:
            return self._run(self._set_user_preferences(request))
        except Exception as e:
            LOGGER.exception("SetUserPreferences failed", exc_info=e)
            return pb2.SetUserPreferencesResponse(success=False, message=str(e))

    @staticmethod
    def _validate_recipient_address(
        channel: NotificationChannel, addr: Optional[str]
    ) -> None:
        if addr is None:
            return
        try:
            if channel == NotificationChannel.EMAIL:
                TypeAdapter(EmailStr).validate_python(addr)
            elif channel == NotificationChannel.WEBHOOK:
                TypeAdapter(AnyUrl).validate_python(addr)
            elif channel == NotificationChannel.WHATSAPP:
                from notification_registry.models.base import PhoneNumber

                PhoneNumber(number=addr)
        except Exception as exc:
            raise ValueError(
                f"Invalid recipient_address for channel {channel.value!r}: {exc}"
            ) from exc

    async def _set_user_preferences(self, request):
        user_id = UUID(request.user_id)
        notification_type = NotificationType(request.notification_type)

        entries = []
        for p in request.preferences:
            channel = NotificationChannel(p.channel)
            addr = p.recipient_address if p.HasField("recipient_address") else None
            if channel == NotificationChannel.PLATFORM:
                addr = None  # PLATFORM uses user_id from payload implicitly
            else:
                self._validate_recipient_address(channel, addr)
            entries.append(
                UserNotificationPreferenceTable(
                    user_id=user_id,
                    notification_type=notification_type,
                    channel=channel,
                    recipient_address=addr,
                )
            )

        async with IOC_CONTAINER(scope=dishka.Scope.REQUEST) as ioc:
            repo = await ioc.get(NotificationRepository)
            await repo.user_preferences.set_preferences(
                user_id, notification_type, entries
            )

        LOGGER.info(
            f"SetUserPreferences: user_id={user_id}, "
            f"notification_type={notification_type.value}, count={len(entries)}"
        )
        return pb2.SetUserPreferencesResponse(
            success=True,
            message=f"Set {len(entries)} preference(s)",
        )


def serve(env: str = "main"):
    configure_logger(__name__, "debug")
    configure_logger("notification_service", "debug")

    LOGGER.info(f"Starting notification-service gRPC server in '{env}' mode")

    start_http_server(NOTIFICATION_SERVICE_CONFIG.prometheus_port)
    LOGGER.info(f"Prometheus metrics on :{NOTIFICATION_SERVICE_CONFIG.prometheus_port}")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = NotificationServiceServicer()
    pb2_grpc.add_NotificationServiceServicer_to_server(servicer, server)
    bind_address = f"[::]:{NOTIFICATION_SERVICE_CONFIG.port}"
    server.add_insecure_port(bind_address)

    def _graceful_shutdown(sig, frame):
        LOGGER.info(f"Received signal {sig}, stopping gRPC server...")
        servicer.close()
        server.stop(grace=30)

    signal.signal(signal.SIGTERM, _graceful_shutdown)
    signal.signal(signal.SIGINT, _graceful_shutdown)

    LOGGER.info(f"gRPC server listening on {bind_address}")
    server.start()
    server.wait_for_termination()
    servicer.close()
    LOGGER.info("gRPC server stopped")


if __name__ == "__main__":
    fire.Fire(serve)
