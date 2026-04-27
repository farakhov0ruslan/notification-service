"""
Tests that enum values are stored as lowercase strings in the database.

PostgreSQL creates the enum type with lowercase values (reset_password, email, normal)
matching the .value of the StrEnum from notification-registry.
SQLAlchemy by default uses the .name of the Python enum (RESET_PASSWORD, EMAIL, NORMAL),
which causes InvalidTextRepresentationError on INSERT in PostgreSQL.

These tests catch the mismatch by reading back the raw stored string from SQLite.
SQLite stores UUIDs as hex strings without hyphens, so we use nid.hex in WHERE.
"""

from uuid import uuid4

from notification_registry import NotificationChannel
from notification_registry import NotificationPriority
from notification_registry import NotificationType
from sqlalchemy import text
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from notification_service.infrastructure.enums import NotificationStatus
from notification_service.infrastructure.models import NotificationTable


def _make_session_maker(engine):
    return async_sessionmaker(class_=AsyncSession, expire_on_commit=False, bind=engine)


async def _insert_and_read_raw(engine, column: str) -> str | None:
    nid = uuid4()
    async with _make_session_maker(engine)() as s:
        s.add(
            NotificationTable(
                id=nid,
                notification_type=NotificationType.RESET_PASSWORD,
                channel=NotificationChannel.EMAIL,
                priority=NotificationPriority.NORMAL,
                status=NotificationStatus.PENDING,
            )
        )
        await s.commit()

    async with _make_session_maker(engine)() as s:
        row = (
            await s.execute(
                text(f'SELECT {column} FROM "NotificationTable" WHERE id = :id'),
                {"id": nid.hex},  # SQLite stores UUID as hex without hyphens
            )
        ).fetchone()

    return row[0] if row else None


async def test_notification_type_stored_as_lowercase_value(engine):
    value = await _insert_and_read_raw(engine, "notification_type")
    assert value == "reset_password", (
        f"Expected 'reset_password' (enum .value) but got {value!r}. "
        "SQLAlchemy is using enum .name — breaks on PostgreSQL."
    )


async def test_channel_stored_as_lowercase_value(engine):
    value = await _insert_and_read_raw(engine, "channel")
    assert value == "email", (
        f"Expected 'email' but got {value!r}. "
        "SQLAlchemy is using enum .name — breaks on PostgreSQL."
    )


async def test_priority_stored_as_lowercase_value(engine):
    value = await _insert_and_read_raw(engine, "priority")
    assert value == "normal", (
        f"Expected 'normal' but got {value!r}. "
        "SQLAlchemy is using enum .name — breaks on PostgreSQL."
    )
