from enum import Enum as EnumType


class NotificationStatus(EnumType):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    @classmethod
    def finished_status(cls) -> tuple["NotificationStatus", ...]:
        return (
            NotificationStatus.SENT,
            NotificationStatus.DELIVERED,
            NotificationStatus.FAILED,
            NotificationStatus.CANCELLED,
        )

    @classmethod
    def active_status(cls) -> tuple["NotificationStatus", ...]:
        return (
            NotificationStatus.PENDING,
            NotificationStatus.QUEUED,
            NotificationStatus.PROCESSING,
        )


class NotificationChannel(EnumType):
    EMAIL = "EMAIL"
    PLATFORM = "PLATFORM"
    WHATSAPP = "WHATSAPP"
    WEBHOOK = "WEBHOOK"


class NotificationType(EnumType):
    SYSTEM_ALERT = "SYSTEM_ALERT"
    USER_WELCOME = "USER_WELCOME"
    USER_PASSWORD_RESET = "USER_PASSWORD_RESET"
    LEAD_UPDATE = "LEAD_UPDATE"
    CAMPAIGN_STATUS = "CAMPAIGN_STATUS"
    REPORT_READY = "REPORT_READY"
    SUBSCRIPTION_EXPIRING = "SUBSCRIPTION_EXPIRING"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    CUSTOM = "CUSTOM"


class NotificationPriority(EnumType):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"