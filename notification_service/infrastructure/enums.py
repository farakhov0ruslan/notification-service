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
