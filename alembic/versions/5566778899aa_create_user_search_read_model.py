"""create user_search_read_model

Revision ID: 5566778899aa
Revises: 88e30aa6e397
Create Date: 2026-09-09 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5566778899aa"
down_revision: str | None = "88e30aa6e397"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema: создать read model поиска пользователей и заполнить его."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "user_search_read_model",
        sa.Column("identity_id", sa.Uuid(), primary_key=True),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=32), nullable=False),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('UTC', NOW())"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["identity_id"], ["identities.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        comment=(
            "Read model для нечёткого поиска пользователей по имени "
            "пользователя; денормализует данные учётной записи и профиля"
        ),
    )

    op.create_index(
        "ix_user_search_read_model_username_trgm",
        "user_search_read_model",
        [sa.text("lower(username) gin_trgm_ops")],
        unique=False,
        postgresql_using="gin",
    )

    op.create_index(
        "ix_user_search_read_model_username_prefix",
        "user_search_read_model",
        [sa.text("lower(username) text_pattern_ops")],
        unique=False,
    )

    op.execute(
        """
        INSERT INTO user_search_read_model (
            identity_id,
            profile_id,
            username,
            display_name,
            avatar_url,
            created_at,
            updated_at
        )
        SELECT
            i.id,
            p.id,
            i.username,
            p.display_name,
            p.avatar_url,
            p.created_at,
            p.updated_at
        FROM identities i
        JOIN profiles p ON p.identity_id = i.id
        """
    )


def downgrade() -> None:
    """Downgrade schema: удалить read model поиска пользователей."""
    op.drop_index(
        "ix_user_search_read_model_username_prefix",
        table_name="user_search_read_model",
    )

    op.drop_index(
        "ix_user_search_read_model_username_trgm",
        table_name="user_search_read_model",
        postgresql_using="gin",
    )

    op.drop_table("user_search_read_model")
