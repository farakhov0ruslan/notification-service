from utils_library.DataBase.driver import DataBaseConfig
from utils_library.DataBase.driver import DatabaseDriver
from utils_library.DataBase.schema import Schema

from notification_service.config import NOTIFICATION_DATABASE


class NotificationDB(Schema):
    @property
    def database(self) -> DataBaseConfig:
        return DataBaseConfig(
            driver=DatabaseDriver.postgres,
            config=NOTIFICATION_DATABASE,
            description="Notification Service Database",
        )

    notification = "notification.data"
