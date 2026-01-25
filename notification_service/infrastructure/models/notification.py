from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import JSON
from sqlalchemy import TEXT
from sqlmodel import Column
from sqlmodel import Enum
from sqlmodel import Field
from sqlmodel import SQLModel
from utils_library.AlchemyRepository import BaseUUIDModel

from notification_service.infrastructure.enums import NotificationChannel
from notification_service.infrastructure.enums import NotificationPriority
from notification_service.infrastructure.enums import NotificationStatus
from notification_service.infrastructure.enums import NotificationType
from notification_service.tables import NotificationDB


class NotificationBase(SQLModel):
    recipient_id: Optional[UUID] = Field(default=None, index=True)
    recipient_email: Optional[str] = Field(
        default=None, sa_column=Column(TEXT, index=True)
    )
    recipient_phone: Optional[str] = Field(
        default=None, sa_column=Column(TEXT, index=True)
    )
    webhook_url: Optional[str] = Field(default=None, sa_column=Column(TEXT))

    notification_type: NotificationType = Field(
        sa_column=Column(
            Enum(
                NotificationType,
                schema=NotificationDB.notification.schema,
                name="notificationtype",
                create_type=True,
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
                create_type=True,
            ),
            index=True,
        )
    )

    priority: NotificationPriority = Field(
        default=NotificationPriority.NORMAL,
        sa_column=Column(
            Enum(
                NotificationPriority,
                schema=NotificationDB.notification.schema,
                name="notificationpriority",
                create_type=True,
            ),
            index=True,
        ),
    )

    status: NotificationStatus = Field(
        default=NotificationStatus.PENDING,
        sa_column=Column(
            Enum(
                NotificationStatus,
                schema=NotificationDB.notification.schema,
                name="notificationstatus",
                create_type=True,
            ),
            index=True,
        ),
    )

    subject: Optional[str] = Field(default=None, sa_column=Column(TEXT))
    body: Optional[str] = Field(default=None, sa_column=Column(TEXT))
    template_id: Optional[str] = Field(default=None, sa_column=Column(TEXT, index=True))
    template_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    next_retry_at: Optional[datetime] = Field(default=None, index=True)

    external_id: Optional[str] = Field(
        default=None, sa_column=Column(TEXT, index=True)
    )
    last_error: Optional[str] = Field(default=None, sa_column=Column(TEXT))

    scheduled_at: Optional[datetime] = Field(default=None, index=True)
    sent_at: Optional[datetime] = Field(default=None)
    delivered_at: Optional[datetime] = Field(default=None)


class NotificationTable(BaseUUIDModel, NotificationBase, table=True):
    pass