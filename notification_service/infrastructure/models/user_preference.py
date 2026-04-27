from typing import Optional
from uuid import UUID

from sqlalchemy import TEXT
from sqlalchemy import UniqueConstraint
from sqlmodel import Column
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

    notification_type: str = Field(sa_column=Column(TEXT, index=True))

    channel: str = Field(sa_column=Column(TEXT, index=True))

    recipient_address: Optional[str] = Field(
        default=None,
        sa_column=Column(TEXT),
        # EMAIL → email address, WEBHOOK → URL, WHATSAPP → phone, PLATFORM → str(user_id)
    )
