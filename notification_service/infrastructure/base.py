from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import registry
from sqlmodel import SQLModel
from utils_library.AlchemyRepository import BASIC_INDEX_MAPPING

from notification_service.tables import NotificationDB

mapper_registry = registry(
    metadata=MetaData(
        naming_convention=BASIC_INDEX_MAPPING,
        schema=NotificationDB.notification.schema,
    ),
)


class NotificationBase(DeclarativeBase):
    registry = mapper_registry
    metadata = mapper_registry.metadata


SQLModel.metadata = NotificationBase.metadata