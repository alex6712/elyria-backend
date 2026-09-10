from typing import Annotated

from pydantic import UUID4, Field, StringConstraints

from src.shared.presentation.http.schemas import BaseJsonModel, PaginationResponse
from src.users.domain.value_objects.avatar_url import AVATAR_URL_MAX_LENGTH
from src.users.domain.value_objects.display_name import (
    DISPLAY_NAME_MAX_LENGTH,
    DISPLAY_NAME_MIN_LENGTH,
)
from src.users.domain.value_objects.username import (
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_PATTERN,
)
from src.users.presentation.http.v1.schemas._helpers import length_description


class UserSearchItem(BaseJsonModel):
    """Элемент результата нечёткого поиска пользователей.

    Содержит данные учётной записи (Identity) и профиля (Profile)
    для одного найденного пользователя.

    Attributes
    ----------
    identity_id : UUID4
        Идентификатор учётной записи пользователя.
    profile_id : UUID4
        Идентификатор профиля пользователя.
    username : str
        Имя пользователя (логин) учётной записи.
    display_name : str
        Отображаемое имя профиля.
    avatar_url : str | None
        URL изображения аватара профиля; ``null`` - аватар не установлен.

    See Also
    --------
    :class:`BaseJsonModel`
        Базовая модель данных, сериализуемых в JSON.
    """

    identity_id: UUID4 = Field(
        description=(
            "Идентификатор учётной записи пользователя " + "(UUID четвёртой версии)."
        ),
        examples=["7c4f0d2e-6a1b-4c5d-9e8f-0a1b2c3d4e5f"],
    )
    profile_id: UUID4 = Field(
        description="Идентификатор профиля пользователя (UUID четвёртой версии).",
        examples=["f2a3c8e1-5b47-4d6e-9c8a-1d3f5e7a9b2c"],
    )
    username: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=USERNAME_MIN_LENGTH,
            max_length=USERNAME_MAX_LENGTH,
            pattern=USERNAME_PATTERN,
        ),
    ] = Field(
        description=(
            "Имя пользователя (логин) ("
            + f"{length_description(USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH)}, "
            + "латинские строчные и заглавные, цифры, дефис и нижнее подчёркивание"
            + ")."
        ),
        examples=["john_doe", "alex_2026"],
    )
    display_name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=DISPLAY_NAME_MIN_LENGTH,
            max_length=DISPLAY_NAME_MAX_LENGTH,
        ),
    ] = Field(
        description=(
            "Отображаемое имя пользователя ("
            + f"{
                length_description(DISPLAY_NAME_MIN_LENGTH, DISPLAY_NAME_MAX_LENGTH)
            }, "
            + "любые Unicode-символы)."
        ),
        examples=["Александр", "7", "一只非常重要的鸡"],
    )
    avatar_url: Annotated[
        str | None,
        StringConstraints(max_length=AVATAR_URL_MAX_LENGTH),
    ] = Field(
        description=(
            "URL изображения аватара (абсолютный URL со схемой http/https, "
            + f"макс. {AVATAR_URL_MAX_LENGTH} символов); значение ``null`` означает, "
            + "что аватар не установлен."
        ),
        examples=["https://cdn.elyria.ru/avatars/john_doe.png", None],
    )


class UserSearchResponse(PaginationResponse):
    """Модель ответа нечёткого поиска пользователей по имени пользователя.

    Расширяет :class:`PaginationResponse` списком найденных
    пользователей.

    Attributes
    ----------
    items : list[UserSearchItem]
        Найденные пользователи (учётная запись + профиль).
    total : int
        Общее количество результатов, соответствующих запросу,
        без учёта ограничений пагинации.

    See Also
    --------
    :class:`PaginationResponse`
        Базовая модель ответа с полями ``code``, ``detail`` и ``total``.
    """

    items: list[UserSearchItem] = Field(
        description="Найденные пользователи.",
        examples=[
            [
                {
                    "identity_id": "7c4f0d2e-6a1b-4c5d-9e8f-0a1b2c3d4e5f",
                    "profile_id": "f2a3c8e1-5b47-4d6e-9c8a-1d3f5e7a9b2c",
                    "username": "john_doe",
                    "display_name": "Джон Доу",
                    "avatar_url": "https://cdn.elyria.ru/avatars/john_doe.png",
                }
            ]
        ],
    )
