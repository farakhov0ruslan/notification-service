from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SendNotificationRequest(_message.Message):
    __slots__ = ("notification_type", "channel", "priority", "recipient_id", "recipient_email", "recipient_phone", "webhook_url", "subject", "payload_json", "scheduled_at")
    NOTIFICATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_ID_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_EMAIL_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_PHONE_FIELD_NUMBER: _ClassVar[int]
    WEBHOOK_URL_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_JSON_FIELD_NUMBER: _ClassVar[int]
    SCHEDULED_AT_FIELD_NUMBER: _ClassVar[int]
    notification_type: str
    channel: str
    priority: str
    recipient_id: str
    recipient_email: str
    recipient_phone: str
    webhook_url: str
    subject: str
    payload_json: str
    scheduled_at: str
    def __init__(self, notification_type: _Optional[str] = ..., channel: _Optional[str] = ..., priority: _Optional[str] = ..., recipient_id: _Optional[str] = ..., recipient_email: _Optional[str] = ..., recipient_phone: _Optional[str] = ..., webhook_url: _Optional[str] = ..., subject: _Optional[str] = ..., payload_json: _Optional[str] = ..., scheduled_at: _Optional[str] = ...) -> None: ...

class SendNotificationResponse(_message.Message):
    __slots__ = ("success", "notification_id", "status", "message", "notification_ids")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    NOTIFICATION_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    NOTIFICATION_IDS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    notification_id: str
    status: str
    message: str
    notification_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, success: bool = ..., notification_id: _Optional[str] = ..., status: _Optional[str] = ..., message: _Optional[str] = ..., notification_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class GetNotificationStatusRequest(_message.Message):
    __slots__ = ("notification_id",)
    NOTIFICATION_ID_FIELD_NUMBER: _ClassVar[int]
    notification_id: str
    def __init__(self, notification_id: _Optional[str] = ...) -> None: ...

class GetNotificationStatusResponse(_message.Message):
    __slots__ = ("success", "notification_id", "status", "channel", "notification_type", "last_error", "retry_count", "scheduled_at", "sent_at", "delivered_at", "created_at")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    NOTIFICATION_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    NOTIFICATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    LAST_ERROR_FIELD_NUMBER: _ClassVar[int]
    RETRY_COUNT_FIELD_NUMBER: _ClassVar[int]
    SCHEDULED_AT_FIELD_NUMBER: _ClassVar[int]
    SENT_AT_FIELD_NUMBER: _ClassVar[int]
    DELIVERED_AT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    success: bool
    notification_id: str
    status: str
    channel: str
    notification_type: str
    last_error: str
    retry_count: int
    scheduled_at: str
    sent_at: str
    delivered_at: str
    created_at: str
    def __init__(self, success: bool = ..., notification_id: _Optional[str] = ..., status: _Optional[str] = ..., channel: _Optional[str] = ..., notification_type: _Optional[str] = ..., last_error: _Optional[str] = ..., retry_count: _Optional[int] = ..., scheduled_at: _Optional[str] = ..., sent_at: _Optional[str] = ..., delivered_at: _Optional[str] = ..., created_at: _Optional[str] = ...) -> None: ...

class CancelNotificationRequest(_message.Message):
    __slots__ = ("notification_id",)
    NOTIFICATION_ID_FIELD_NUMBER: _ClassVar[int]
    notification_id: str
    def __init__(self, notification_id: _Optional[str] = ...) -> None: ...

class CancelNotificationResponse(_message.Message):
    __slots__ = ("success", "notification_id", "status", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    NOTIFICATION_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    notification_id: str
    status: str
    message: str
    def __init__(self, success: bool = ..., notification_id: _Optional[str] = ..., status: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class ListNotificationsRequest(_message.Message):
    __slots__ = ("recipient_id", "status", "channel", "limit", "offset")
    RECIPIENT_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    recipient_id: str
    status: str
    channel: str
    limit: int
    offset: int
    def __init__(self, recipient_id: _Optional[str] = ..., status: _Optional[str] = ..., channel: _Optional[str] = ..., limit: _Optional[int] = ..., offset: _Optional[int] = ...) -> None: ...

class NotificationItem(_message.Message):
    __slots__ = ("notification_id", "notification_type", "channel", "priority", "status", "recipient_id", "recipient_email", "subject", "last_error", "retry_count", "scheduled_at", "sent_at", "delivered_at", "created_at")
    NOTIFICATION_ID_FIELD_NUMBER: _ClassVar[int]
    NOTIFICATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_ID_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_EMAIL_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_FIELD_NUMBER: _ClassVar[int]
    LAST_ERROR_FIELD_NUMBER: _ClassVar[int]
    RETRY_COUNT_FIELD_NUMBER: _ClassVar[int]
    SCHEDULED_AT_FIELD_NUMBER: _ClassVar[int]
    SENT_AT_FIELD_NUMBER: _ClassVar[int]
    DELIVERED_AT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    notification_id: str
    notification_type: str
    channel: str
    priority: str
    status: str
    recipient_id: str
    recipient_email: str
    subject: str
    last_error: str
    retry_count: int
    scheduled_at: str
    sent_at: str
    delivered_at: str
    created_at: str
    def __init__(self, notification_id: _Optional[str] = ..., notification_type: _Optional[str] = ..., channel: _Optional[str] = ..., priority: _Optional[str] = ..., status: _Optional[str] = ..., recipient_id: _Optional[str] = ..., recipient_email: _Optional[str] = ..., subject: _Optional[str] = ..., last_error: _Optional[str] = ..., retry_count: _Optional[int] = ..., scheduled_at: _Optional[str] = ..., sent_at: _Optional[str] = ..., delivered_at: _Optional[str] = ..., created_at: _Optional[str] = ...) -> None: ...

class ListNotificationsResponse(_message.Message):
    __slots__ = ("success", "notifications", "total")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    NOTIFICATIONS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    success: bool
    notifications: _containers.RepeatedCompositeFieldContainer[NotificationItem]
    total: int
    def __init__(self, success: bool = ..., notifications: _Optional[_Iterable[_Union[NotificationItem, _Mapping]]] = ..., total: _Optional[int] = ...) -> None: ...

class UserPreferenceItem(_message.Message):
    __slots__ = ("user_id", "notification_type", "channel", "recipient_address")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    NOTIFICATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    notification_type: str
    channel: str
    recipient_address: str
    def __init__(self, user_id: _Optional[str] = ..., notification_type: _Optional[str] = ..., channel: _Optional[str] = ..., recipient_address: _Optional[str] = ...) -> None: ...

class GetUserPreferencesRequest(_message.Message):
    __slots__ = ("user_id", "notification_type")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    NOTIFICATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    notification_type: str
    def __init__(self, user_id: _Optional[str] = ..., notification_type: _Optional[str] = ...) -> None: ...

class GetUserPreferencesResponse(_message.Message):
    __slots__ = ("success", "preferences")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    PREFERENCES_FIELD_NUMBER: _ClassVar[int]
    success: bool
    preferences: _containers.RepeatedCompositeFieldContainer[UserPreferenceItem]
    def __init__(self, success: bool = ..., preferences: _Optional[_Iterable[_Union[UserPreferenceItem, _Mapping]]] = ...) -> None: ...

class SetUserPreferencesRequest(_message.Message):
    __slots__ = ("user_id", "notification_type", "preferences")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    NOTIFICATION_TYPE_FIELD_NUMBER: _ClassVar[int]
    PREFERENCES_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    notification_type: str
    preferences: _containers.RepeatedCompositeFieldContainer[UserPreferenceItem]
    def __init__(self, user_id: _Optional[str] = ..., notification_type: _Optional[str] = ..., preferences: _Optional[_Iterable[_Union[UserPreferenceItem, _Mapping]]] = ...) -> None: ...

class SetUserPreferencesResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...
