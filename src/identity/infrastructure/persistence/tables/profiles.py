from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.types import String, Uuid

from src.identity.domain.value_objects.display_name import DISPLAY_NAME_MAX_LENGTH
from src.shared.infrastructure.persistence import metadata
from src.shared.infrastructure.persistence.columns import base_columns

profiles_table = Table(
    "profiles",
    metadata,
    *base_columns(),
    Column(
        "identity_id",
        Uuid(),
        ForeignKey("identities.id", ondelete="CASCADE"),
        nullable=False,
        comment="Ссылка на учётную запись пользователя (identities.id)",
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
        String(512),
        nullable=True,
        comment="URL изображения аватара пользователя",
    ),
    comment="Профили пользователей системы",
)
"""Таблица профилей пользователей.

Содержит профильную информацию пользователя: отображаемое имя
и ссылку на изображение аватара. Связана с таблицей `identities`
по внешнему ключу `user_id` (при удалении учётной записи профиль
удаляется каскадно).

Notes
-----
Учётные данные для аутентификации (логин, хэш пароля) в этой
таблице не хранятся - они находятся в таблице `identities`.
"""
