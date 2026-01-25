from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from notification_service.infrastructure.base import NotificationBase


class BasicTable(NotificationBase):
    __tablename__ = "basic_table"
    id: Mapped[int] = mapped_column(primary_key=True)