"""users divided to identities and profiles

Revision ID: 88e30aa6e397
Revises: 08aed751a5ba
Create Date: 2026-07-31 08:43:37.897315

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '88e30aa6e397'
down_revision: str | None = '08aed751a5ba'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Имена внешних ключей legacy-таблиц, ссылающихся на users.id.
# Сгенерированы СУБД автоматически как '<table>_<column>_fkey'.
_LEGACY_USER_FKEYS: list[tuple[str, str, str]] = [
    ('files', 'files_created_by_fkey', 'created_by'),
    ('albums', 'albums_created_by_fkey', 'created_by'),
    ('notes', 'notes_created_by_fkey', 'created_by'),
    ('couple_members', 'couple_members_user_id_fkey', 'user_id'),
    ('couple_requests', 'couple_requests_initiator_id_fkey', 'initiator_id'),
    ('couple_requests', 'couple_requests_recipient_id_fkey', 'recipient_id'),
]
"""Констрейнты, удаляемые вместе с таблицей ``users``.

Каждый элемент - кортеж ``(таблица, имя_констрейнта, колонка)``.
Таблицы остаются в схеме (у них нет представления в коде проекта),
но теряют внешние ключи на ``users.id`` в соответствии с принципом
изоляции ограниченных контекстов.
"""


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('identities',
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Уникальный идентификатор записи'),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='Дата и время изменения записи'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('UTC', NOW())"), nullable=False, comment='Дата и время создания записи'),
    sa.Column('username', sa.String(length=32), nullable=False, comment='Уникальный логин (макс. 32 символа)'),
    sa.Column('password_hash', sa.String(length=128), nullable=False, comment='Хэш пароля пользователя'),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False, comment='Признак активности учётной записи'),
    sa.Column('version', sa.Integer(), server_default=sa.text('1'), nullable=False, comment='Версия агрегата для optimistic locking'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username', name='uq_identities_username'),
    comment='Учётные записи (идентификационные данные) пользователей'
    )
    op.create_index('ix_identities_is_active', 'identities', ['is_active'], unique=False)
    op.create_table('profiles',
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Уникальный идентификатор записи'),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='Дата и время изменения записи'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('UTC', NOW())"), nullable=False, comment='Дата и время создания записи'),
    sa.Column('identity_id', sa.Uuid(), nullable=False, comment='Ссылка на учётную запись пользователя (identities.id)'),
    sa.Column('display_name', sa.String(length=32), nullable=False, comment='Отображаемое имя пользователя (макс. 32 символов)'),
    sa.Column('avatar_url', sa.String(length=512), nullable=True, comment='URL изображения аватара пользователя'),
    sa.Column('version', sa.Integer(), server_default=sa.text('1'), nullable=False, comment='Версия агрегата для optimistic locking'),
    sa.ForeignKeyConstraint(['identity_id'], ['identities.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    comment='Профили пользователей системы'
    )
    op.execute(
        """
        INSERT INTO identities (id, username, password_hash, is_active, created_at, updated_at)
        SELECT id, username, password_hash, is_active, created_at, updated_at
        FROM users
        """
    )
    op.execute(
        """
        INSERT INTO profiles (identity_id, display_name, avatar_url, created_at, updated_at)
        SELECT id, display_name, avatar_url, created_at, updated_at
        FROM users
        """
    )
    op.add_column('sessions', sa.Column('version', sa.Integer(), server_default=sa.text('1'), nullable=False, comment='Версия агрегата для optimistic locking'))
    op.alter_column('sessions', 'user_id', new_column_name='identity_id')
    op.drop_constraint(op.f('sessions_user_id_fkey'), 'sessions', type_='foreignkey')
    op.create_foreign_key(op.f('sessions_identity_id_fkey'), 'sessions', 'identities', ['identity_id'], ['id'], ondelete='CASCADE')
    op.drop_index(op.f('ix_sessions_user_id'), table_name='sessions')
    op.create_index('ix_sessions_identity_id', 'sessions', ['identity_id'], unique=False)
    for table, constraint, _ in _LEGACY_USER_FKEYS:
        op.drop_constraint(op.f(constraint), table, type_='foreignkey')
    op.drop_index(op.f('ix_users_is_active'), table_name='users')
    op.drop_table('users')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table('users',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False, comment='Уникальный идентификатор записи'),
    sa.Column('username', sa.VARCHAR(length=32), autoincrement=False, nullable=False, comment='Уникальный логин (макс. 32 символа)'),
    sa.Column('password_hash', sa.VARCHAR(length=128), autoincrement=False, nullable=False, comment='Хэш пароля пользователя'),
    sa.Column('is_active', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False, comment='Признак активности учётной записи'),
    sa.Column('avatar_url', sa.VARCHAR(length=512), autoincrement=False, nullable=True, comment='URL изображения аватара пользователя'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('UTC', NOW())"), autoincrement=False, nullable=False, comment='Дата и время создания записи'),
    sa.Column('display_name', sa.VARCHAR(length=32), autoincrement=False, nullable=False, comment='Отображаемое имя пользователя (макс. 32 символов)'),
    sa.Column('updated_at', sa.DateTime(timezone=True), autoincrement=False, nullable=True, comment='Дата и время изменения записи'),
    sa.Column('public_key', sa.LargeBinary(), autoincrement=False, nullable=True, comment='Публичный ключ пользователя для сквозного шифрования'),
    sa.Column('encrypted_private_key', sa.LargeBinary(), autoincrement=False, nullable=True, comment='Приватный ключ пользователя, зашифрованный мастер-ключом'),
    sa.Column('private_key_nonce', sa.LargeBinary(), autoincrement=False, nullable=True, comment='Nonce, использованный при шифровании приватного ключа'),
    sa.Column('kdf_salt', sa.LargeBinary(), autoincrement=False, nullable=True, comment='Случайная соль для функции получения ключа'),
    sa.Column('kdf_params', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True, comment='Параметры получения мастер-ключа из пароля'),
    sa.PrimaryKeyConstraint('id', name=op.f('users_pkey')),
    sa.UniqueConstraint('username', name=op.f('uq_users_username')),
    comment='Аутентифицированные пользователи системы'
    )
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)
    op.execute(
        """
        INSERT INTO users (id, username, password_hash, is_active, avatar_url, display_name, created_at, updated_at)
        SELECT i.id, i.username, i.password_hash, i.is_active, p.avatar_url, p.display_name, i.created_at, i.updated_at
        FROM identities i
        JOIN profiles p ON p.identity_id = i.id
        """
    )
    for table, constraint, column in _LEGACY_USER_FKEYS:
        op.create_foreign_key(op.f(constraint), table, 'users', [column], ['id'], ondelete='CASCADE')
    op.drop_constraint(op.f('sessions_identity_id_fkey'), 'sessions', type_='foreignkey')
    op.drop_index('ix_sessions_identity_id', table_name='sessions')
    op.alter_column('sessions', 'identity_id', new_column_name='user_id')
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)
    op.create_foreign_key(op.f('sessions_user_id_fkey'), 'sessions', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.drop_column('sessions', 'version')
    op.drop_index('ix_identities_is_active', table_name='identities')
    op.drop_table('profiles')
    op.drop_table('identities')
