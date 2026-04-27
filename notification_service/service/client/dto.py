from typing import Optional

from notification_registry import BaseNotificationPayload
from notification_registry import NotificationChannel
from notification_registry import NotificationPriority
from notification_registry import NotificationType
from pydantic import BaseModel

from notification_service.infrastructure.enums import NotificationStatus


class SendNotificationRequest(BaseModel):
    notification_type: NotificationType | str
    channel: NotificationChannel | str | None = (
        None  # optional: resolved from preferences when absent
    )
    payload: BaseNotificationPayload
    priority: NotificationPriority | str | None = None
    recipient_id: str | None = None
    recipient_address: str | None = None
    scheduled_at: str | None = None

    model_config = {"arbitrary_types_allowed": True}


class SendNotificationResult(BaseModel):
    success: bool
    notification_id: str
    status: str
    message: str
    notification_ids: list[str] = []


class UserPreference(BaseModel):
    user_id: str
    notification_type: str
    channel: str
    recipient_address: Optional[str] = None


class GetUserPreferencesResult(BaseModel):
    success: bool
    preferences: list[UserPreference] = []


class SetUserPreferencesResult(BaseModel):
    success: bool
    message: str


class NotificationStatusResult(BaseModel):
    success: bool
    notification_id: str
    status: Optional[str] = None
    channel: Optional[str] = None
    notification_type: Optional[str] = None
    last_error: Optional[str] = None
    scheduled_at: Optional[str] = None
    sent_at: Optional[str] = None
    created_at: Optional[str] = None

    @property
    def is_sent(self) -> bool:
        return self.status == NotificationStatus.SENT.value

    @property
    def is_failed(self) -> bool:
        return self.status == NotificationStatus.FAILED.value

    @property
    def is_pending(self) -> bool:
        return self.status == NotificationStatus.PENDING.value


class CancelNotificationResult(BaseModel):
    success: bool
    notification_id: str
    status: str
    message: str


class NotificationItem(BaseModel):
    notification_id: str
    notification_type: str
    channel: str
    priority: str
    status: str
    recipient_id: Optional[str] = None
    recipient_address: Optional[str] = None
    last_error: Optional[str] = None
    scheduled_at: Optional[str] = None
    sent_at: Optional[str] = None
    created_at: str


class ListNotificationsResult(BaseModel):
    success: bool
    notifications: list[NotificationItem]
    total: int
