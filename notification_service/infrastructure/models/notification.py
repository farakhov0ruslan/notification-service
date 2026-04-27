from datetime import datetime
from typing import Optional
from uuid import UUID

from notification_registry import NotificationPriority
from sqlalchemy import TEXT
from sqlmodel import Column
from sqlmodel import Enum
from sqlmodel import Field
from sqlmodel import SQLModel
from utils_library.AlchemyRepository import BaseUUIDModel

from notification_service.infrastructure.enums import NotificationStatus
from notification_service.tables import NotificationDB


class NotificationBase(SQLModel):
    recipient_id: Optional[UUID] = Field(default=None, index=True)
    recipient_address: Optional[str] = Field(
        default=None, sa_column=Column(TEXT, index=True)
    )

    notification_type: str = Field(sa_column=Column(TEXT, index=True))

    channel: str = Field(sa_column=Column(TEXT, index=True))

    priority: NotificationPriority = Field(
        default=NotificationPriority.NORMAL,
        sa_column=Column(
            Enum(
                NotificationPriority,
                schema=NotificationDB.notification.schema,
                name="notificationpriority",
                create_type=True,
                values_callable=lambda x: [e.value for e in x],
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

    body: Optional[str] = Field(default=None, sa_column=Column(TEXT))

    external_id: Optional[str] = Field(default=None, sa_column=Column(TEXT, index=True))
    last_error: Optional[str] = Field(default=None, sa_column=Column(TEXT))

    scheduled_at: Optional[datetime] = Field(default=None, index=True)
    sent_at: Optional[datetime] = Field(default=None)


class NotificationTable(BaseUUIDModel, NotificationBase, table=True):
    pass
