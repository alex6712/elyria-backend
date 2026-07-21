from sqlalchemy import Column, Index, Table, UniqueConstraint, text
from sqlalchemy.types import Boolean, String

from src.identity.domain.value_objects.username import USERNAME_MAX_LENGTH
from src.shared.infrastructure.persistence import metadata
from src.shared.infrastructure.persistence.columns import base_columns

identities_table = Table(
    "identities",
    metadata,
    *base_columns(),
    Column(
        "username",
        String(USERNAME_MAX_LENGTH),
        nullable=False,
        comment=f"Уникальный логин (макс. {USERNAME_MAX_LENGTH} символа)",
    ),
    Column(
        "password_hash",
        String(128),
        nullable=False,
        comment="Хэш пароля пользователя",
    ),
    Column(
        "is_active",
        Boolean(),
        nullable=False,
        server_default=text("true"),
        comment="Признак активности учётной записи",
    ),
    UniqueConstraint("username", name="uq_identities_username"),
    Index("ix_identities_is_active", "is_active"),
    comment="Учётные записи (идентификационные данные) пользователей",
)
"""Таблица учётных записей пользователей.

Хранит данные, необходимые для аутентификации: логин, хэш пароля
и признак активности учётной записи.

Notes
-----
Профильная информация (отображаемое имя, аватар и т. п.) в этой
таблице не хранится - она вынесена в таблицу `profiles`,
связанную с `identities` по внешнему ключу `user_id`.
"""
