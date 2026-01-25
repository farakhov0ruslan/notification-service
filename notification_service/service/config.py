from dataclasses import dataclass
from dataclasses import field

from utils_library.Configuration.meta_config import AbstractMetaConfig


@dataclass
class NotificationServiceConfig(AbstractMetaConfig):
    host: str = field(
        default="localhost",
        metadata={
            "docs": "gRPC server host",
            "required": False,
        },
    )
    port: int = field(
        default=46600,
        metadata={
            "docs": "gRPC server port",
            "required": False,
        },
    )
    prometheus_port: int = field(
        default=9092,
        metadata={
            "docs": "Prometheus metrics port",
            "required": False,
        },
    )


NOTIFICATION_SERVICE_CONFIG = NotificationServiceConfig()