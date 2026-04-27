import asyncio
import contextlib
import signal
import threading

import dishka
import fire
from notification_registry import RabbitMQNotificationClient
from notification_registry import deserialize_message
from prometheus_client import start_http_server
from utils_library.Logging.log import configure_logger
from utils_library.Logging.log import get_logger
from utils_library.RabbitMQ.correct_consumer import RabbitConsumer
from utils_library.RabbitMQ.correct_consumer import ThreadedRabbitConsumer
from utils_library.RabbitMQ.rabbitmq import RABBIT_MQ_CONFIG

from notification_service.dispatcher import dispatch
from notification_service.infrastructure.enums import NotificationStatus
from notification_service.ioc import IOC_CONTAINER
from notification_service.ioc import NotificationRepository
from notification_service.router.config import NOTIFICATION_ROUTER_CONFIG

LOGGER = get_logger(__name__)


class NotificationRouter:
    """
    Reads NotificationMessage from notification.general, routes to channel-specific queue.
    Updates notification status: PENDING → SENT after successful publish.
    """

    def __init__(self):
        self._client = RabbitMQNotificationClient(rabbit_config=RABBIT_MQ_CONFIG)
        self._consumer = RabbitConsumer(
            queue_name=NOTIFICATION_ROUTER_CONFIG.input_queue,
            on_message=self._handle_message,
            rabbitmq_config=RABBIT_MQ_CONFIG,
            max_retries=NOTIFICATION_ROUTER_CONFIG.max_retries,
            retry_delay=NOTIFICATION_ROUTER_CONFIG.retry_delay,
        )
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._loop_thread.start()
        LOGGER.debug("NotificationRouter initialized, async loop thread started")

    def _handle_message(self, body: bytes) -> None:
        LOGGER.debug(
            f"Message received from queue ({len(body)} bytes), dispatching to async loop"
        )
        future = asyncio.run_coroutine_threadsafe(
            self._handle_message_async(body), self._loop
        )
        future.result()

    async def _handle_message_async(self, body: bytes) -> None:
        message = deserialize_message(body)
        nid = message.metadata.notification_id
        LOGGER.debug(
            f"Processing message: id={nid}, "
            f"type={message.metadata.notification_type.value}, "
            f"channel={message.metadata.channel.value}"
        )

        try:
            async with IOC_CONTAINER(scope=dishka.Scope.REQUEST) as ioc:
                repo = await ioc.get(NotificationRepository)
                notification = await repo.notifications.get(id=nid)

                if notification is None:
                    LOGGER.error(f"Notification {nid} not found in DB, skipping")
                    return

                if notification.status != NotificationStatus.PENDING:
                    LOGGER.warning(
                        f"Notification {nid} already in status={notification.status.value}, skipping"
                    )
                    return

                LOGGER.info(
                    f"Routing {nid} → channel={message.metadata.channel.value}, "
                    f"queue={message.metadata.channel.queue_name!r}"
                )
                dispatch(message, client=self._client)

                await repo.notifications.update_status(nid, NotificationStatus.SENT)
                LOGGER.info(f"Notification {nid} routed successfully, status=SENT")
        except Exception:
            LOGGER.exception(f"Failed to process notification {nid}, will retry")
            raise

    def run(self) -> None:
        LOGGER.info(
            f"Starting Notification Router, "
            f"listening on {NOTIFICATION_ROUTER_CONFIG.input_queue!r}"
        )
        self._client.start()
        LOGGER.debug("RabbitMQ notification client started")
        threaded = ThreadedRabbitConsumer(self._consumer)

        def _shutdown(signum, _frame) -> None:
            LOGGER.info(f"Received signal {signum}, shutting down router...")
            threaded.stop()
            self._loop.call_soon_threadsafe(self._loop.stop)

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        LOGGER.info("Router is running, waiting for messages...")
        threaded.start()
        threaded.join()

        LOGGER.info("Router consumer stopped, closing RabbitMQ client...")
        with contextlib.suppress(Exception):
            self._client.close()
        LOGGER.info("Router shut down cleanly")

    def stop(self) -> None:
        LOGGER.info("Stopping router...")
        self._consumer.stop()
        self._loop.call_soon_threadsafe(self._loop.stop)
        with contextlib.suppress(Exception):
            self._client.close()


def serve(env: str = "main"):
    configure_logger(__name__, "debug")
    configure_logger("notification_service", "debug")

    LOGGER.info(f"Starting notification-service Router in '{env}' mode")
    start_http_server(NOTIFICATION_ROUTER_CONFIG.metrics_port)
    LOGGER.info(f"Prometheus metrics on :{NOTIFICATION_ROUTER_CONFIG.metrics_port}")
    NotificationRouter().run()


if __name__ == "__main__":
    fire.Fire(serve)
