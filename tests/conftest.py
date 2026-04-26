import asyncio
from unittest.mock import patch

import dishka
import pytest
import pytest_asyncio
import sqlalchemy
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel.ext.asyncio.session import AsyncSession

from notification_service.infrastructure.base import NotificationBase
from notification_service.ioc import IOC_CONTAINER
from notification_service.ioc import NotificationRepository
from notification_service.ioc import NotificationStorageSession
from tests.utils.factories import AnalyticsPayloadFactory
from tests.utils.factories import LinkedInDisconnectedPayloadFactory
from tests.utils.factories import ResetPasswordPayloadFactory


def make_session_maker(engine):
    return async_sessionmaker(
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=engine,
    )


@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    return tmp_path_factory.mktemp("db") / "test_notification.sqlite"


@pytest.fixture(scope="session", autouse=True)
def engine(db_path):
    _engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        echo=False,
        execution_options={"schema_translate_map": {"notification": None}},
        poolclass=NullPool,
    )

    async def _setup():
        async with _engine.begin() as conn:
            await conn.run_sync(NotificationBase.metadata.drop_all)
        async with _engine.begin() as conn:
            await conn.run_sync(NotificationBase.metadata.create_all)
            result = await conn.execute(
                sqlalchemy.text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            print(f"\nSQLite tables created: {[r[0] for r in result.fetchall()]}")

    asyncio.run(_setup())
    yield _engine
    asyncio.run(_engine.dispose())


@pytest.fixture(scope="session", autouse=True)
def patch_pool(engine):
    """Redirect NOTIFICATION_POOL to SQLite for the entire test session."""
    def fake_pool():
        return make_session_maker(engine)

    with patch("notification_service.ioc.NOTIFICATION_POOL", fake_pool):
        yield


@pytest.fixture(scope="session")
def base_ioc_container():
    return IOC_CONTAINER


@pytest_asyncio.fixture(scope="function")
async def ioc_container(base_ioc_container):
    async with base_ioc_container(scope=dishka.Scope.REQUEST) as container:
        yield container


@pytest_asyncio.fixture(scope="function")
async def full_repo(ioc_container):
    return await ioc_container.get(NotificationRepository)


@pytest_asyncio.fixture(scope="function")
async def session(ioc_container):
    s = await ioc_container.get(NotificationStorageSession)
    yield s
    await s.rollback()


@pytest.fixture
def reset_password_payload():
    return ResetPasswordPayloadFactory.build()


@pytest.fixture
def analytics_payload():
    return AnalyticsPayloadFactory.build()


@pytest.fixture
def linkedin_disconnected_payload():
    return LinkedInDisconnectedPayloadFactory.build()
