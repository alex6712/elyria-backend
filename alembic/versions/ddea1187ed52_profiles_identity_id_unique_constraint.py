"""profiles identity_id unique constraint

Revision ID: ddea1187ed52
Revises: 5566778899aa
Create Date: 2026-09-14 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ddea1187ed52"
down_revision: str | None = "5566778899aa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CONSTRAINT_NAME = "uq_profiles_identity_id"
"""Имя ограничения уникальности ``profiles.identity_id``."""


def upgrade() -> None:
    """Создать ограничение уникальности ``profiles.identity_id``.

    Перед созданием ограничения проверяет, что у каждой учётной записи
    существует не более одного профиля. При наличии дубликатов миграция
    прерывается с явной ошибкой, не изменяя схему: разрешение конфликта
    данных является ручным решением и не выполняется автоматически.
    """
    connection = op.get_bind()

    duplicates = connection.execute(
        sa.text(
            "SELECT identity_id, COUNT(*) AS cnt "
            +"FROM profiles "
            +"GROUP BY identity_id "
            +"HAVING COUNT(*) > 1"
        )
    ).mappings()

    offending: list[tuple[str, int]] = [
        (str(row["identity_id"]), row["cnt"]) for row in duplicates
    ]

    if offending:
        details = ", ".join(f"{identity_id} ({cnt})" for identity_id, cnt in offending)
        raise RuntimeError(
            "Cannot create unique constraint "
            + f"{_CONSTRAINT_NAME!r}: duplicate profiles exist for identities "
            + f"{details}. Resolve duplicates before applying this migration."
        )

    op.create_unique_constraint(_CONSTRAINT_NAME, "profiles", ["identity_id"])


def downgrade() -> None:
    """Снять ограничение уникальности ``profiles.identity_id``."""
    op.drop_constraint(_CONSTRAINT_NAME, "profiles", type_="unique")
