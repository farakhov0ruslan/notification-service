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
class RabbitMQConfiguration(AbstractMetaConfig):
    host: str = field(
        default="127.0.0.1",
        metadata={
            "docs": "RabbitMQ host",
            "required": False,
        },
    )

    port: int = field(
        default=5672,
        metadata={
            "docs": "RabbitMQ port",
            "required": False,
        },
    )

    user: str = field(
        default="guest",
        metadata={
            "docs": "RabbitMQ user",
            "required": False,
            "hidden": True,
        },
    )

    password: str = field(
        default="guest",
        metadata={
            "docs": "RabbitMQ password",
            "required": False,
            "hidden": True,
        },
    )

    virtual_host: str = field(
        default="/",
        metadata={
            "docs": "RabbitMQ virtual host",
            "required": False,
        },
    )

    email_queue: str = field(
        default="notification.email",
        metadata={
            "docs": "Email notification queue name",
            "required": False,
        },
    )

    platform_queue: str = field(
        default="notification.platform",
        metadata={
            "docs": "Platform notification queue name",
            "required": False,
        },
    )

    whatsapp_queue: str = field(
        default="notification.whatsapp",
        metadata={
            "docs": "WhatsApp notification queue name",
            "required": False,
        },
    )

    webhook_queue: str = field(
        default="notification.webhook",
        metadata={
            "docs": "Webhook notification queue name",
            "required": False,
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
RABBITMQ_CONFIG = RabbitMQConfiguration()
NOTIFICATION_RETRY = NotificationRetryConfiguration()