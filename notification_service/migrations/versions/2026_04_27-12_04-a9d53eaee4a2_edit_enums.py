"""edit enums

Revision ID: a9d53eaee4a2
Revises: 6faa66019d15
Create Date: 2026-04-27 12:04:38.457845

"""

from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a9d53eaee4a2"
down_revision: Union[str, Sequence[str], None] = "6faa66019d15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Сначала конвертируем все колонки из ENUM в TEXT, только потом дропаем типы
    op.alter_column(
        "NotificationTable",
        "notification_type",
        existing_type=postgresql.ENUM(
            "analytics",
            "reset_password",
            "linkedin_disconnected",
            "delivery_failed",
            "greeting",
            name="notificationtype",
            schema="notification",
        ),
        type_=sa.TEXT(),
        existing_nullable=True,
        postgresql_using="notification_type::text",
        schema="notification",
    )
    op.alter_column(
        "NotificationTable",
        "channel",
        existing_type=postgresql.ENUM(
            "email",
            "platform",
            "webhook",
            "whatsapp",
            name="notificationchannel",
            schema="notification",
        ),
        type_=sa.TEXT(),
        existing_nullable=True,
        postgresql_using="channel::text",
        schema="notification",
    )
    op.alter_column(
        "UserNotificationPreferenceTable",
        "notification_type",
        existing_type=postgresql.ENUM(
            "analytics",
            "reset_password",
            "linkedin_disconnected",
            "delivery_failed",
            "greeting",
            name="notificationtype",
            schema="notification",
        ),
        type_=sa.TEXT(),
        existing_nullable=True,
        postgresql_using="notification_type::text",
        schema="notification",
    )
    op.alter_column(
        "UserNotificationPreferenceTable",
        "channel",
        existing_type=postgresql.ENUM(
            "email",
            "platform",
            "webhook",
            "whatsapp",
            name="notificationchannel",
            schema="notification",
        ),
        type_=sa.TEXT(),
        existing_nullable=True,
        postgresql_using="channel::text",
        schema="notification",
    )
    # Теперь можно дропать типы — колонки уже отвязаны
    sa.Enum(
        "email",
        "platform",
        "webhook",
        "whatsapp",
        name="notificationchannel",
        schema="notification",
    ).drop(op.get_bind())
    sa.Enum(
        "analytics",
        "reset_password",
        "linkedin_disconnected",
        "delivery_failed",
        "greeting",
        name="notificationtype",
        schema="notification",
    ).drop(op.get_bind())
    op.add_column(
        "NotificationTable",
        sa.Column("recipient_address", sa.TEXT(), nullable=True),
        schema="notification",
    )
    op.drop_index(
        op.f("ix_notification_NotificationTable_next_retry_at"),
        table_name="NotificationTable",
        schema="notification",
    )
    op.drop_index(
        op.f("ix_notification_NotificationTable_recipient_email"),
        table_name="NotificationTable",
        schema="notification",
    )
    op.drop_index(
        op.f("ix_notification_NotificationTable_recipient_phone"),
        table_name="NotificationTable",
        schema="notification",
    )
    op.create_index(
        op.f("ix_notification_NotificationTable_recipient_address"),
        "NotificationTable",
        ["recipient_address"],
        unique=False,
        schema="notification",
    )
    op.drop_column("NotificationTable", "webhook_url", schema="notification")
    op.drop_column("NotificationTable", "recipient_email", schema="notification")
    op.drop_column("NotificationTable", "recipient_phone", schema="notification")
    op.drop_column("NotificationTable", "subject", schema="notification")
    op.drop_column("NotificationTable", "next_retry_at", schema="notification")
    op.drop_column("NotificationTable", "max_retries", schema="notification")
    op.drop_column("NotificationTable", "retry_count", schema="notification")


def downgrade() -> None:
    """Downgrade schema."""
    # Сначала воссоздаём ENUM типы, потом конвертируем колонки обратно
    sa.Enum(
        "email",
        "platform",
        "webhook",
        "whatsapp",
        name="notificationchannel",
        schema="notification",
    ).create(op.get_bind())
    sa.Enum(
        "analytics",
        "reset_password",
        "linkedin_disconnected",
        "delivery_failed",
        "greeting",
        name="notificationtype",
        schema="notification",
    ).create(op.get_bind())
    op.drop_column("NotificationTable", "recipient_address", schema="notification")
    op.drop_index(
        op.f("ix_notification_NotificationTable_recipient_address"),
        table_name="NotificationTable",
        schema="notification",
    )
    op.add_column(
        "NotificationTable",
        sa.Column("retry_count", sa.INTEGER(), autoincrement=False, nullable=False),
        schema="notification",
    )
    op.add_column(
        "NotificationTable",
        sa.Column("max_retries", sa.INTEGER(), autoincrement=False, nullable=False),
        schema="notification",
    )
    op.add_column(
        "NotificationTable",
        sa.Column(
            "next_retry_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        schema="notification",
    )
    op.add_column(
        "NotificationTable",
        sa.Column("subject", sa.TEXT(), autoincrement=False, nullable=True),
        schema="notification",
    )
    op.add_column(
        "NotificationTable",
        sa.Column("recipient_phone", sa.TEXT(), autoincrement=False, nullable=True),
        schema="notification",
    )
    op.add_column(
        "NotificationTable",
        sa.Column("recipient_email", sa.TEXT(), autoincrement=False, nullable=True),
        schema="notification",
    )
    op.add_column(
        "NotificationTable",
        sa.Column("webhook_url", sa.TEXT(), autoincrement=False, nullable=True),
        schema="notification",
    )
    op.create_index(
        op.f("ix_notification_NotificationTable_recipient_phone"),
        "NotificationTable",
        ["recipient_phone"],
        unique=False,
        schema="notification",
    )
    op.create_index(
        op.f("ix_notification_NotificationTable_recipient_email"),
        "NotificationTable",
        ["recipient_email"],
        unique=False,
        schema="notification",
    )
    op.create_index(
        op.f("ix_notification_NotificationTable_next_retry_at"),
        "NotificationTable",
        ["next_retry_at"],
        unique=False,
        schema="notification",
    )
    op.alter_column(
        "NotificationTable",
        "notification_type",
        existing_type=sa.TEXT(),
        type_=postgresql.ENUM(
            "analytics",
            "reset_password",
            "linkedin_disconnected",
            "delivery_failed",
            "greeting",
            name="notificationtype",
            schema="notification",
        ),
        existing_nullable=True,
        postgresql_using="notification_type::notification.notificationtype",
        schema="notification",
    )
    op.alter_column(
        "NotificationTable",
        "channel",
        existing_type=sa.TEXT(),
        type_=postgresql.ENUM(
            "email",
            "platform",
            "webhook",
            "whatsapp",
            name="notificationchannel",
            schema="notification",
        ),
        existing_nullable=True,
        postgresql_using="channel::notification.notificationchannel",
        schema="notification",
    )
    op.alter_column(
        "UserNotificationPreferenceTable",
        "notification_type",
        existing_type=sa.TEXT(),
        type_=postgresql.ENUM(
            "analytics",
            "reset_password",
            "linkedin_disconnected",
            "delivery_failed",
            "greeting",
            name="notificationtype",
            schema="notification",
        ),
        existing_nullable=True,
        postgresql_using="notification_type::notification.notificationtype",
        schema="notification",
    )
    op.alter_column(
        "UserNotificationPreferenceTable",
        "channel",
        existing_type=sa.TEXT(),
        type_=postgresql.ENUM(
            "email",
            "platform",
            "webhook",
            "whatsapp",
            name="notificationchannel",
            schema="notification",
        ),
        existing_nullable=True,
        postgresql_using="channel::notification.notificationchannel",
        schema="notification",
    )
