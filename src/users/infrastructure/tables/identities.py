from sqlalchemy import Column, Index, Table, UniqueConstraint, text
from sqlalchemy.types import Boolean, String

from src.shared.infrastructure import metadata
from src.shared.infrastructure.columns import (
    audit_columns,
    identifier_column,
    version_column,
)
from src.users.domain.value_objects.email import EMAIL_MAX_LENGTH
from src.users.domain.value_objects.username import USERNAME_MAX_LENGTH

identities_table = Table(
    "identities",
    metadata,
    identifier_column("random"),
    Column(
        "username",
        String(USERNAME_MAX_LENGTH),
        nullable=False,
        comment=f"Уникальный логин (макс. {USERNAME_MAX_LENGTH} символа)",
    ),
    Column(
        "email",
        String(EMAIL_MAX_LENGTH),
        nullable=False,
        comment=(
            "Email пользователя (нормализованный: в нижнем регистре, "
            + f"макс. {EMAIL_MAX_LENGTH} символа)"
        ),
    ),
    Column(
        "email_verified",
        Boolean(),
        nullable=False,
        server_default=text("false"),
        comment="Признак подтверждения адреса электронной почты",
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
    *audit_columns(),
    version_column(),
    UniqueConstraint("username", name="uq_identities_username"),
    Index("ix_identities_is_active", "is_active"),
    Index("uq_identities_email_lower", text("lower(email)"), unique=True),
    comment="Учётные записи (идентификационные данные) пользователей",
)
"""Таблица учётных записей пользователей.

Хранит данные, необходимые для аутентификации: логин, адрес
электронной почты, хэш пароля и признак активности учётной записи.

Notes
-----
Профильная информация (отображаемое имя, аватар и т. п.) в этой
таблице не хранится - она вынесена в таблицу `profiles`,
связанную с `identities` по внешнему ключу `identity_id`.
"""
