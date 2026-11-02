"""verification tokens table added

Revision ID: 626c5878118d
Revises: 4e8ae78f3981
Create Date: 2026-11-02 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '626c5878118d'
down_revision: str | None = '4e8ae78f3981'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'verification_tokens',
        sa.Column(
            'id',
            sa.Uuid(),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
            comment='Уникальный идентификатор записи',
        ),
        sa.Column(
            'identity_id',
            sa.Uuid(),
            nullable=False,
            comment='Идентификатор учётной записи, которой выдан токен',
        ),
        sa.Column(
            'token_hash',
            sa.String(length=128),
            nullable=False,
            comment='Криптографический хеш токена подтверждения',
        ),
        sa.Column(
            'purpose',
            sa.Enum('email_verification', name='verification_token_purpose'),
            nullable=False,
            comment='Назначение токена подтверждения',
        ),
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=False,
            comment='Дата и время истечения срока действия токена',
        ),
        sa.Column(
            'used_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Дата и время применения или аннулирования токена',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('UTC', NOW())"),
            nullable=False,
            comment='Дата и время создания записи',
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Дата и время изменения записи',
        ),
        sa.ForeignKeyConstraint(
            ['identity_id'],
            ['identities.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'token_hash',
            name='uq_verification_tokens_token_hash',
        ),
        comment='Токены подтверждения операций пользователей',
    )
    op.create_index(
        'ix_verification_tokens_identity_id',
        'verification_tokens',
        ['identity_id'],
        unique=False,
    )
    op.create_index(
        'ix_verification_tokens_expires_at',
        'verification_tokens',
        ['expires_at'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        'ix_verification_tokens_expires_at',
        table_name='verification_tokens',
    )
    op.drop_index(
        'ix_verification_tokens_identity_id',
        table_name='verification_tokens',
    )
    op.drop_table('verification_tokens')
    op.execute('DROP TYPE verification_token_purpose')
