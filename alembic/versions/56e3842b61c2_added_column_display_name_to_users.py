"""added column display_name to users

Revision ID: 56e3842b61c2
Revises: ec7dac4fccee
Create Date: 2026-07-01 11:48:49.575970

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56e3842b61c2'
down_revision: Union[str, None] = 'ec7dac4fccee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "display_name",
            sa.String(length=64),
            nullable=True,
            comment="Отображаемое имя пользователя",
        ),
    )
    op.execute("""
        UPDATE users
        SET display_name = username
        WHERE display_name IS NULL
    """)
    op.alter_column(
        "users",
        "display_name",
        nullable=False,
    )
    op.alter_column('users', 'username',
               existing_type=sa.VARCHAR(length=64),
               type_=sa.String(length=32),
               comment='Уникальный логин (макс. 32 символа)',
               existing_comment='Уникальный логин (макс. 64 символа)',
               existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('users', 'username',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=64),
               comment='Уникальный логин (макс. 64 символа)',
               existing_comment='Уникальный логин (макс. 32 символа)',
               existing_nullable=False)
    op.drop_column('users', 'display_name')
