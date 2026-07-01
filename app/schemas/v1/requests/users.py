from pydantic import BaseModel, Field

from app.core.types import UNSET, Maybe
from app.core.validation import ValidatedDisplayName


class PatchProfileRequest(BaseModel):
    """Схема запроса на частичное редактирование профиля пользователя.

    Используется в качестве представления данных для частичного
    обновления полей профиля пользователя. Все поля опциональны -
    передаются только те атрибуты, которые необходимо изменить.

    Attributes
    ----------
    display_name : Maybe[str]
        Отображаемое имя пользователя. Если не передан - остаётся `UNSET`
        и текущее значение в базе данных не изменяется.
    avatar_url : Maybe[str]
        URL аватара пользователя. Если не передан - остаётся `UNSET`
        и текущее значение в базе данных не изменяется.
    """

    display_name: Maybe[ValidatedDisplayName] = Field(
        default_factory=lambda: UNSET,
        description="Новое отображаемое имя пользователя",
        examples=["Владислав", "88005553535", "الاسم", "👨⚒👨‍👧‍👦⏮🗿🦀🚀"],
    )
    avatar_url: Maybe[str] = Field(
        default_factory=lambda: UNSET,
        description="URL аватара пользователя",
        examples=[
            "https://avatars.githubusercontent.com/u/22058897?s=400&u=46b96191222ac11e6afda1648ad912384d8a8a30&v=4"
        ],
    )
