"""email columns in identities

Revision ID: 4e8ae78f3981
Revises: ddea1187ed52
Create Date: 2026-09-15 15:08:01.410623

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4e8ae78f3981'
down_revision: str | None = 'ddea1187ed52'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'identities',
        sa.Column(
            'email',
            sa.String(length=254),
            nullable=True,
            comment=(
                'Email пользователя (нормализованный: в нижнем регистре, '
                'макс. 254 символа)'
            ),
        ),
    )
    op.add_column(
        'identities',
        sa.Column(
            'email_verified',
            sa.Boolean(),
            server_default=sa.text('false'),
            nullable=False,
            comment='Признак подтверждения адреса электронной почты',
        ),
    )
    # Username уникален без учёта регистра, поэтому lower(username) может
    # совпадать у разных учётных записей (например, John и john). Таким
    # вариантам добавляется суффикс +N, чтобы не нарушить уникальный
    # индекс uq_identities_email_lower на lower(email).
    op.execute(
        """
        UPDATE identities i
        SET email = ranked.email
        FROM (
            SELECT
                id,
                lower(username) || '@legacy.invalid'
                    || CASE WHEN rn > 1 THEN '+' || (rn - 1) ELSE '' END AS email
            FROM (
                SELECT
                    id,
                    username,
                    ROW_NUMBER() OVER (
                        PARTITION BY lower(username)
                        ORDER BY created_at, id
                    ) AS rn
                FROM identities
            ) AS numbered
        ) AS ranked
        WHERE i.id = ranked.id
        """
    )
    op.alter_column('identities', 'email', nullable=False)
    op.create_index(
        'uq_identities_email_lower',
        'identities',
        [sa.text('lower(email)')],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_identities_email_lower', table_name='identities')
    op.drop_column('identities', 'email_verified')
    op.drop_column('identities', 'email')