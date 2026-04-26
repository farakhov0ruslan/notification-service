from typing import Optional
from uuid import UUID

from notification_registry import NotificationChannel
from notification_registry import NotificationType
from sqlalchemy import TEXT
from sqlalchemy import UniqueConstraint
from sqlmodel import Column
from sqlmodel import Enum
from sqlmodel import Field
from utils_library.AlchemyRepository import BaseUUIDModel

from notification_service.tables import NotificationDB


class UserNotificationPreferenceTable(BaseUUIDModel, table=True):
    """
    Per-user delivery preferences per (notification_type, channel).

    recipient_address stores the channel-specific destination
    (mirrors NotificationChannel.recipient_field):
      EMAIL    → email address
      WEBHOOK  → webhook URL
      WHATSAPP → phone number
      PLATFORM → str(user_id)  (routing is implicit; stored for record-keeping)
    """

    __table_args__ = (
        UniqueConstraint("user_id", "notification_type", "channel"),
        {"schema": NotificationDB.notification.schema},
    )

    user_id: UUID = Field(index=True)

    notification_type: NotificationType = Field(
        sa_column=Column(
            Enum(
                NotificationType,
                schema=NotificationDB.notification.schema,
                name="notificationtype",
                create_type=False,
            ),
            index=True,
        )
    )

    channel: NotificationChannel = Field(
        sa_column=Column(
            Enum(
                NotificationChannel,
                schema=NotificationDB.notification.schema,
                name="notificationchannel",
                create_type=False,
            ),
            index=True,
        )
    )

    recipient_address: Optional[str] = Field(
        default=None,
        sa_column=Column(TEXT),
        # EMAIL → email address, WEBHOOK → URL, WHATSAPP → phone, PLATFORM → str(user_id)
    )
