"""users table refactor

Revision ID: 08aed751a5ba
Revises: 9c859fd8c955
Create Date: 2026-07-12 12:09:44.480258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '08aed751a5ba'
down_revision: Union[str, None] = '9c859fd8c955'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('sessions',
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Уникальный идентификатор записи'),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='Дата и время изменения записи'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('UTC', NOW())"), nullable=False, comment='Дата и время создания записи'),
    sa.Column('user_id', sa.Uuid(), nullable=False, comment='Уникальный идентификатор пользователя'),
    sa.Column('session_secret', sa.String(length=128), nullable=False, comment='Уникальный секрет сессии'),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, comment='Дата и время истечения срока действия сессии'),
    sa.Column('last_used_at', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('UTC', NOW())"), nullable=False, comment='Дата и время последнего успешного продления сессии'),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True, comment='Дата и время принудительного завершения сессии'),
    sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP-адрес, с которого была создана сессия'),
    sa.Column('user_agent', sa.String(length=512), nullable=True, comment='User-Agent клиента при создании сессии'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('session_secret', name='uq_sessions_session_secret'),
    comment='Активные и завершённые пользовательские сессии'
    )
    op.create_index('ix_sessions_expires_at', 'sessions', ['expires_at'], unique=False)
    op.create_index('ix_sessions_user_id', 'sessions', ['user_id'], unique=False)
    op.drop_index(op.f('ix_user_sessions_refresh_token_hash'), table_name='user_sessions')
    op.drop_table('user_sessions')
    op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='Дата и время изменения записи'))
    op.add_column('users', sa.Column('public_key', sa.LargeBinary(), nullable=True, comment='Публичный ключ пользователя для сквозного шифрования'))
    op.add_column('users', sa.Column('encrypted_private_key', sa.LargeBinary(), nullable=True, comment='Приватный ключ пользователя, зашифрованный мастер-ключом'))
    op.add_column('users', sa.Column('private_key_nonce', sa.LargeBinary(), nullable=True, comment='Nonce, использованный при шифровании приватного ключа'))
    op.add_column('users', sa.Column('kdf_salt', sa.LargeBinary(), nullable=True, comment='Случайная соль для функции получения ключа'))
    op.add_column('users', sa.Column('kdf_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Параметры получения мастер-ключа из пароля'))
    op.alter_column('users', 'password_hash',
               existing_type=sa.VARCHAR(length=128),
               comment='Хэш пароля пользователя',
               existing_comment='Хэш пароля (Argon2id через Passlib)',
               existing_nullable=False)
    op.alter_column('users', 'avatar_url',
               existing_type=sa.VARCHAR(length=512),
               comment='URL изображения аватара пользователя',
               existing_comment='URL аватара пользователя',
               existing_nullable=True)
    op.alter_column('users', 'is_active',
               existing_type=sa.BOOLEAN(),
               comment='Признак активности учётной записи',
               existing_comment='Статус пользователя (активный или заблокирован)',
               existing_nullable=False,
               existing_server_default=sa.text('true'))
    op.drop_index(op.f('ix_users_username'), table_name='users')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    op.alter_column('users', 'is_active',
               existing_type=sa.BOOLEAN(),
               comment='Статус пользователя (активный или заблокирован)',
               existing_comment='Признак активности учётной записи',
               existing_nullable=False,
               existing_server_default=sa.text('true'))
    op.alter_column('users', 'avatar_url',
               existing_type=sa.VARCHAR(length=512),
               comment='URL аватара пользователя',
               existing_comment='URL изображения аватара пользователя',
               existing_nullable=True)
    op.alter_column('users', 'password_hash',
               existing_type=sa.VARCHAR(length=128),
               comment='Хэш пароля (Argon2id через Passlib)',
               existing_comment='Хэш пароля пользователя',
               existing_nullable=False)
    op.drop_column('users', 'kdf_params')
    op.drop_column('users', 'kdf_salt')
    op.drop_column('users', 'private_key_nonce')
    op.drop_column('users', 'encrypted_private_key')
    op.drop_column('users', 'public_key')
    op.drop_column('users', 'updated_at')
    op.create_table('user_sessions',
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False, comment='Уникальный идентификатор пользователя'),
    sa.Column('refresh_token_hash', sa.VARCHAR(length=128), autoincrement=False, nullable=False, comment='Хэш токена обновления (HMAC-SHA256)'),
    sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False, comment='Дата и время, когда токен будет просрочен'),
    sa.Column('last_used_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False, comment='Дата и время последнего обновления сессии'),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False, comment='Уникальный идентификатор записи'),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text("timezone('UTC'::text, now())"), autoincrement=False, nullable=False, comment='Дата и время создания записи'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('user_sessions_user_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('user_sessions_pkey')),
    comment='Информация о пользовательских сессиях'
    )
    op.create_index(op.f('ix_user_sessions_refresh_token_hash'), 'user_sessions', ['refresh_token_hash'], unique=False)
    op.drop_index('ix_sessions_user_id', table_name='sessions')
    op.drop_index('ix_sessions_expires_at', table_name='sessions')
    op.drop_table('sessions')
