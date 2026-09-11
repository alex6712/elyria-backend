from sqlalchemy import Column, ForeignKey, Index, Table, text
from sqlalchemy.types import String, Uuid

from src.shared.infrastructure import metadata
from src.shared.infrastructure.columns import audit_columns
from src.users.domain.value_objects.avatar_url import AVATAR_URL_MAX_LENGTH
from src.users.domain.value_objects.display_name import DISPLAY_NAME_MAX_LENGTH
from src.users.domain.value_objects.username import USERNAME_MAX_LENGTH

user_search_read_model = Table(
    "user_search_read_model",
    metadata,
    Column(
        "identity_id",
        Uuid(),
        ForeignKey("identities.id", ondelete="CASCADE"),
        primary_key=True,
        comment=(
            "Идентификатор учётной записи (identities.id), естественный ключ read model"
        ),
    ),
    Column(
        "profile_id",
        Uuid(),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        comment="Идентификатор профиля (profiles.id)",
    ),
    Column(
        "username",
        String(USERNAME_MAX_LENGTH),
        nullable=False,
        comment=f"Имя пользователя (логин), макс. {USERNAME_MAX_LENGTH} символа",
    ),
    Column(
        "display_name",
        String(DISPLAY_NAME_MAX_LENGTH),
        nullable=False,
        comment=(
            f"Отображаемое имя пользователя (макс. {DISPLAY_NAME_MAX_LENGTH} символов)"
        ),
    ),
    Column(
        "avatar_url",
        String(AVATAR_URL_MAX_LENGTH),
        nullable=True,
        comment="URL изображения аватара пользователя",
    ),
    *audit_columns(),
    Index(
        "ix_user_search_read_model_username_trgm",
        text("lower(username) gin_trgm_ops"),
        postgresql_using="gin",
    ),
    Index(
        "ix_user_search_read_model_username_prefix",
        text("lower(username) text_pattern_ops"),
    ),
    comment=(
        "Read model для нечёткого поиска пользователей по имени "
        "пользователя; денормализует данные учётной записи и профиля"
    ),
)
"""Read model таблица для поиска пользователей по username.

Денормализованное представление, объединяющее данные учётной записи
(``identities.username``) и профиля (``profiles.display_name``,
``profiles.avatar_url``) для нечёткого поиска. Обслуживается обработчиками
доменных событий (eventual consistency) после успешного коммита операций
регистрации и изменения профиля.

Key ``identity_id`` является естественным первичным ключом, поскольку
read model находится в отношении 1:1 с учётной записью.
"""
