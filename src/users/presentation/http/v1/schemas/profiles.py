from typing import Annotated

from pydantic import Field, StringConstraints, field_validator

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
