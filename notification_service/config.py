from dataclasses import dataclass
from dataclasses import field

from utils_library.Configuration.meta_config import AbstractMetaConfig


@dataclass
class NotificationDatabaseConfiguration(AbstractMetaConfig):
    db_host: str = field(
        default="127.0.0.1",
        metadata={
            "docs": "HOST",
            "required": False,
        },
    )

    db_port: int = field(
        default=5432,
        metadata={
            "docs": "PORT",
            "required": False,
        },
    )

    db_user: str = field(
        default="postgres",
        metadata={
            "docs": "db user",
            "required": False,
            "hidden": True,
        },
    )
    db_pwd: str = field(
        default="postgres",
        metadata={
            "docs": "db pwd",
            "required": False,
            "hidden": True,
        },
    )

    db_name: str = field(
        default="notification_db",
        metadata={
            "docs": "database name",
            "required": False,
            "hidden": False,
        },
    )


@dataclass
class NotificationRetryConfiguration(AbstractMetaConfig):
    max_retries: int = field(
        default=3,
        metadata={
            "docs": "Maximum number of retry attempts",
            "required": False,
        },
    )

    retry_delay_seconds: int = field(
        default=60,
        metadata={
            "docs": "Initial delay between retries in seconds",
            "required": False,
        },
    )

    retry_backoff_multiplier: float = field(
        default=2.0,
        metadata={
            "docs": "Multiplier for exponential backoff",
            "required": False,
        },
    )


NOTIFICATION_DATABASE = NotificationDatabaseConfiguration()
NOTIFICATION_RETRY = NotificationRetryConfiguration()
