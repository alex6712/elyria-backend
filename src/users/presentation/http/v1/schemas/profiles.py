from datetime import datetime
from typing import Annotated

from pydantic import UUID4, Field, StringConstraints, field_validator

from src.shared.presentation.http.schemas import BaseJsonModel
from src.users.domain.value_objects.avatar_url import (
    AVATAR_URL_MAX_LENGTH,
    AVATAR_URL_MIN_LENGTH,
)
from src.users.domain.value_objects.display_name import (
    DISPLAY_NAME_MAX_LENGTH,
    DISPLAY_NAME_MIN_LENGTH,
)
from src.users.presentation.http.v1.schemas._helpers import length_description


class ChangeProfileRequest(BaseJsonModel):
    """Схема запроса изменения профиля пользователя.

    Частичная схема (PATCH): все поля необязательны. Отсутствие поля
    в теле запроса означает, что соответствующий атрибут профиля
    изменять не требуется; явная передача ``null`` для ``avatarUrl``
    означает удаление аватара.

    Attributes
    ----------
    display_name : str | None
        Строковое представление нового отображаемого имени пользователя.
    avatar_url : str | None
        Строковое представление нового URL изображения аватара;
        ``null`` - удалить аватар из профиля.

    Notes
    -----
    Для отображаемого имени пользователя (display_name) ведущие
    и завершающие пробельные символы удаляются перед обработкой.
    Явная передача ``null`` в ``display_name`` недопустима
    (отображаемое имя является обязательным атрибутом профиля)
    и приводит к ошибке валидации 422.

    See Also
    --------
    :class:`BaseJsonModel`
        Базовая модель данных, сериализуемых в JSON.
    """

    display_name: Annotated[
        str | None,
        StringConstraints(
            strip_whitespace=True,
            min_length=DISPLAY_NAME_MIN_LENGTH,
            max_length=DISPLAY_NAME_MAX_LENGTH,
        ),
    ] = Field(
        default=None,
        description=(
            "Новое отображаемое имя пользователя ("
            + f"{
                length_description(DISPLAY_NAME_MIN_LENGTH, DISPLAY_NAME_MAX_LENGTH)
            }, "
            + "любые Unicode-символы). Поле необязательно: отсутствие поля "
            + "означает, что имя изменять не требуется."
        ),
        examples=["Александр", "7", "一只非常重要的鸡", "🍆"],
    )

    @field_validator("display_name")
    @classmethod
    def _display_name_is_not_null(cls, value: str | None) -> str | None:
        """Запретить явную передачу ``null`` в ``display_name``.

        Parameters
        ----------
        value : str | None
            Переданное значение поля.

        Returns
        -------
        str | None
            Переданное значение без изменений.

        Raises
        ------
        ValueError
            Если значение равно ``None``: отображаемое имя является
            обязательным атрибутом профиля и не может быть удалено.
        """
        if value is None:
            raise ValueError("display_name cannot be null.")

        return value

    avatar_url: Annotated[
        str | None,
        StringConstraints(
            min_length=AVATAR_URL_MIN_LENGTH, max_length=AVATAR_URL_MAX_LENGTH
        ),
    ] = Field(
        default=None,
        description=(
            "Новый URL изображения аватара ("
            + f"{length_description(AVATAR_URL_MIN_LENGTH, AVATAR_URL_MAX_LENGTH)}, "
            + "абсолютный URL со схемой http/https). Поле необязательно: "
            + "отсутствие поля означает, что аватар изменять не требуется, "
            + "а значение ``null`` - удалить аватар из профиля."
        ),
        examples=["https://cdn.elyria.ru/avatars/john_doe.png", None],
    )


class ProfileResponse(BaseJsonModel):
    """Схема ответа с данными профиля пользователя.

    Содержит отображаемые атрибуты профиля. Технические атрибуты,
    относящиеся к внутренней реализации, в ответ не включаются.

    Attributes
    ----------
    id : UUID4
        Уникальный идентификатор профиля.
    display_name : str
        Отображаемое имя пользователя.
    avatar_url : str | None
        URL изображения аватара; ``null`` - аватар не установлен.
    created_at : datetime
        Дата и время создания профиля.
    updated_at : datetime | None
        Дата и время последнего изменения профиля; ``null`` - профиль
        не изменялся после создания.

    See Also
    --------
    :class:`BaseJsonModel`
        Базовая модель данных, сериализуемых в JSON.
    """

    id: UUID4 = Field(
        description="Уникальный идентификатор профиля (UUID четвёртой версии).",
        examples=["f2a3c8e1-5b47-4d6e-9c8a-1d3f5e7a9b2c"],
    )
    display_name: str = Field(
        description=(
            "Отображаемое имя пользователя ("
            + f"{
                length_description(DISPLAY_NAME_MIN_LENGTH, DISPLAY_NAME_MAX_LENGTH)
            }, "
            + "любые Unicode-символы)."
        ),
        examples=["Александр", "7", "一只非常重要的鸡", "🍆"],
    )
    avatar_url: str | None = Field(
        description=(
            "URL изображения аватара ("
            + f"{length_description(AVATAR_URL_MIN_LENGTH, AVATAR_URL_MAX_LENGTH)}, "
            + "абсолютный URL со схемой http/https); значение ``null`` означает, "
            + "что аватар не установлен."
        ),
        examples=["https://cdn.elyria.ru/avatars/john_doe.png", None],
    )
    created_at: datetime = Field(
        description="Дата и время создания профиля (UTC).",
        examples=["2026-08-24T12:34:56.789012Z"],
    )
    updated_at: datetime | None = Field(
        description=(
            "Дата и время последнего изменения профиля (UTC); "
            "``null`` - профиль не изменялся после создания."
        ),
        examples=["2026-08-24T15:00:00.123456Z", None],
    )
