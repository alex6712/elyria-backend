from sqlalchemy import CheckConstraint, Column, Index, Table, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import Boolean, LargeBinary, String

from src.identity.domain.value_objects.display_name import DISPLAY_NAME_MAX_LENGTH
from src.identity.domain.value_objects.username import USERNAME_MAX_LENGTH
from src.shared.infrastructure.persistence.sqlalchemy import metadata
from src.shared.infrastructure.persistence.sqlalchemy._columns import base_columns

users_table = Table(
    "users",
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
        "public_key",
        LargeBinary(),
        nullable=True,
        comment="Публичный ключ пользователя для сквозного шифрования",
    ),
    Column(
        "encrypted_private_key",
        LargeBinary(),
        nullable=True,
        comment="Приватный ключ пользователя, зашифрованный мастер-ключом",
    ),
    Column(
        "private_key_nonce",
        LargeBinary(),
        nullable=True,
        comment="Nonce, использованный при шифровании приватного ключа",
    ),
    Column(
        "kdf_salt",
        LargeBinary(),
        nullable=True,
        comment="Случайная соль для функции получения ключа",
    ),
    Column(
        "kdf_params",
        JSONB(),
        nullable=True,
        comment="Параметры получения мастер-ключа из пароля",
    ),
    Column(
        "display_name",
        String(DISPLAY_NAME_MAX_LENGTH),
        nullable=False,
        comment=f"Отображаемое имя пользователя (макс. {DISPLAY_NAME_MAX_LENGTH} символов)",
    ),
    Column(
        "avatar_url",
        String(512),
        nullable=True,
        comment="URL изображения аватара пользователя",
    ),
    Column(
        "is_active",
        Boolean(),
        nullable=False,
        server_default=text("true"),
        comment="Признак активности учётной записи",
    ),
    CheckConstraint(
        """
        (
            public_key IS NULL
            AND encrypted_private_key IS NULL
            AND private_key_nonce IS NULL
            AND kdf_salt IS NULL
            AND kdf_params IS NULL
        )
        OR
        (
            public_key IS NOT NULL
            AND encrypted_private_key IS NOT NULL
            AND private_key_nonce IS NOT NULL
            AND kdf_salt IS NOT NULL
            AND kdf_params IS NOT NULL
        )
        """,
        name="ck_users_e2ee_columns_consistent",
    ),
    UniqueConstraint("username", name="uq_users_username"),
    Index("ix_users_is_active", "is_active"),
    comment="Аутентифицированные пользователи системы",
)
"""Таблица зарегистрированных пользователей приложения.

Содержит учётные данные пользователя, профильную информацию,
а также криптографические материалы, необходимые для
сквозного шифрования (E2EE).

Notes
-----
Таблица является корневой для большинства пользовательских
данных. При создании пользователя криптографические поля могут
оставаться пустыми до завершения инициализации E2EE.
"""
