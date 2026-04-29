from dataclasses import dataclass
from dataclasses import field

from utils_library.Configuration.meta_config import AbstractMetaConfig


@dataclass
class NotificationRouterConfig(AbstractMetaConfig):
    input_queue: str = field(
        default="notification.general",
        metadata={
            "docs": "General queue where gRPC server publishes messages",
            "required": False,
        },
    )

    max_retries: int = field(
        default=3,
        metadata={
            "docs": "Maximum retry attempts for routing a message",
            "required": False,
        },
    )

    retry_delay: float = field(
        default=1.0,
        metadata={
            "docs": "Delay between retries in seconds",
            "required": False,
        },
    )

    metrics_port: int = field(
        default=9090,
        metadata={
            "docs": "Prometheus metrics port",
            "required": False,
        },
    )


NOTIFICATION_ROUTER_CONFIG = NotificationRouterConfig()
