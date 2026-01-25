from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import NewType

import sqlalchemy
from dishka import Provider
from dishka import Scope
from dishka import make_async_container
from dishka import provide
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from utils_library.AlchemyRepository import crud
from utils_library.DataBase.configurations import DataBaseConfig
from utils_library.DataBase.schema import DataBaseEngine

from notification_service.infrastructure.crud import CRUDNotification
from notification_service.infrastructure.models import NotificationTable
from notification_service.tables import NotificationDB

NotificationStorageSession = NewType("NotificationStorageSession", AsyncSession)


@dataclass
class NotificationRepository:
    notifications: CRUDNotification


def new_session_maker(
    config: DataBaseConfig,
) -> async_sessionmaker[NotificationStorageSession]:
    connection_str = (
        DataBaseEngine(config).connection_link.render_as_string(hide_password=False)
    ).replace("%", "%%")
    connection_str = connection_str.replace("psycopg2", "asyncpg")
    engine = create_async_engine(connection_str)
    session = async_sessionmaker(
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=engine,
    )
    return session


NOTIFICATION_POOL = lambda: new_session_maker(  # noqa: E731
    config=NotificationDB.notification.database
)


class PoolProvider(Provider):
    @provide(scope=Scope.APP)
    def notification_pool(self) -> async_sessionmaker[NotificationStorageSession]:
        return NOTIFICATION_POOL()


class DataBaseProvider(Provider):
    @provide(scope=Scope.SESSION)
    async def get_session(
        self, pool: async_sessionmaker[NotificationStorageSession]
    ) -> AsyncGenerator[NotificationStorageSession]:
        async with pool(expire_on_commit=False, autoflush=False) as session:
            yield session


class NotificationStorageProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def notifications_repo(
        self, async_session: NotificationStorageSession
    ) -> CRUDNotification:
        return crud.build_dependency_repository(CRUDNotification, NotificationTable)(
            async_session
        )

    @provide(scope=Scope.REQUEST)
    async def full_repo(
        self,
        notifications: CRUDNotification,
    ) -> NotificationRepository:
        return NotificationRepository(
            notifications=notifications,
        )


IOC_CONTAINER = make_async_container(
    PoolProvider(), DataBaseProvider(), NotificationStorageProvider()
)


async def main() -> None:
    async with (
        IOC_CONTAINER(scope=Scope.SESSION) as up_layer,
        up_layer(scope=Scope.REQUEST) as ioc,
    ):
        session = await ioc.get(NotificationStorageSession)
        _ = await session.exec(sqlalchemy.text("SELECT 1"))
        print("Connection successful!")  # noqa


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())