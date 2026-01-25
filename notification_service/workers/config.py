from dataclasses import dataclass
from dataclasses import field

from utils_library.CronRunner import CronDefault


@dataclass()
class NotificationWorkerConfig(CronDefault):
    expire_time_seconds: int = 10 * 60
    schedule_seconds: int = field(default=30, metadata={})
    metrics_port: int = field(
        default=9091,
        metadata={
            "docs": "Port for Prometheus metrics collection",
            "required": False,
        },
    )
    batch_size: int = field(
        default=100,
        metadata={
            "docs": "Number of notifications to process in each batch",
            "required": False,
        },
    )


NOTIFICATION_WORKER_CONFIG = NotificationWorkerConfig()