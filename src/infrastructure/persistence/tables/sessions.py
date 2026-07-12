from sqlalchemy import Column, ForeignKey, Index, Table, UniqueConstraint, text
from sqlalchemy.types import DateTime, String, Uuid

from src.infrastructure.persistence.tables._columns import base_columns
from src.infrastructure.persistence.tables.metadata import metadata

sessions_table = Table(
    "sessions",
    metadata,
    *base_columns(),
    Column(
        "user_id",
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Уникальный идентификатор пользователя",
    ),
    Column(
        "session_secret",
        String(128),
        nullable=False,
        comment="Уникальный секрет сессии",
    ),
    Column(
        "expires_at",
        DateTime(timezone=True),
        nullable=False,
        comment="Дата и время истечения срока действия сессии",
    ),
    Column(
        "last_used_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=text("TIMEZONE('UTC', NOW())"),
        comment="Дата и время последнего успешного продления сессии",
    ),
    Column(
        "revoked_at",
        DateTime(timezone=True),
        nullable=True,
        comment="Дата и время принудительного завершения сессии",
    ),
    Column(
        "ip_address",
        String(45),
        nullable=True,
        comment="IP-адрес, с которого была создана сессия",
    ),
    Column(
        "user_agent",
        String(512),
        nullable=True,
        comment="User-Agent клиента при создании сессии",
    ),
    UniqueConstraint("session_secret", name="uq_sessions_session_secret"),
    Index("ix_sessions_user_id", "user_id"),
    Index("ix_sessions_expires_at", "expires_at"),
    comment="Активные и завершённые пользовательские сессии",
)
"""Таблица пользовательских сессий приложения.

Содержит данные о сессиях аутентифицированных пользователей:
секрет сессии, срок действия, метаданные клиента (IP-адрес,
User-Agent), а также отметки о последнем продлении и
принудительном завершении сессии.

Notes
-----
Каждая сессия связана с пользователем через `user_id` и
удаляется каскадно при удалении соответствующей записи в
таблице `users`. Поле `revoked_at` остаётся пустым для
активных сессий и заполняется при их принудительном
завершении (например, при выходе пользователя из системы
или отзыве доступа администратором).
"""
