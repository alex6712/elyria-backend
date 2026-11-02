from enum import Enum as PyEnum

from sqlalchemy import Column, Enum, ForeignKey, Index, Table, UniqueConstraint
from sqlalchemy.types import DateTime, String, Uuid

from src.shared.infrastructure.columns import audit_columns, identifier_column
from src.shared.infrastructure.metadata import metadata
from src.users.domain.value_objects import VerificationTokenPurpose


def _purpose_values(enum_cls: type[PyEnum]) -> list[str]:
    """Вернуть строковые значения членов перечисления.

    Parameters
    ----------
    enum_cls : type[PyEnum]
        Класс перечисления, значения членов которого требуется
        получить.

    Returns
    -------
    list[str]
        Строковые значения членов перечисления в порядке объявления.
    """
    return [str(member.value) for member in enum_cls]


verification_tokens_table = Table(
    "verification_tokens",
    metadata,
    identifier_column("random"),
    Column(
        "identity_id",
        Uuid(),
        ForeignKey("identities.id", ondelete="CASCADE"),
        nullable=False,
        comment="Идентификатор учётной записи, которой выдан токен",
    ),
    Column(
        "token_hash",
        String(128),
        nullable=False,
        comment="Криптографический хеш токена подтверждения",
    ),
    Column(
        "purpose",
        Enum(
            VerificationTokenPurpose,
            name="verification_token_purpose",
            native_enum=True,
            values_callable=_purpose_values,
        ),
        nullable=False,
        comment="Назначение токена подтверждения",
    ),
    Column(
        "expires_at",
        DateTime(timezone=True),
        nullable=False,
        comment="Дата и время истечения срока действия токена",
    ),
    Column(
        "used_at",
        DateTime(timezone=True),
        nullable=True,
        comment="Дата и время применения или аннулирования токена",
    ),
    *audit_columns(),
    UniqueConstraint("token_hash", name="uq_verification_tokens_token_hash"),
    Index("ix_verification_tokens_identity_id", "identity_id"),
    Index("ix_verification_tokens_expires_at", "expires_at"),
    comment="Токены подтверждения операций пользователей",
)
"""Таблица токенов подтверждения операций пользователей.

Содержит одноразовые токены, подтверждающие выполнение операций,
требующих проверки их инициатора. В таблице хранится только
криптографический хеш токена; открытое значение токена не
сохраняется.

Notes
-----
Каждый токен связан с учётной записью через `identity_id` и
удаляется каскадно при удалении соответствующей записи в таблице
`identities`. Поле `used_at` остаётся пустым для пригодных токенов
и заполняется как при применении токена, так и при его
аннулировании.
"""
