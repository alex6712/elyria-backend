from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from src.shared.presentation.http.schemas import BaseJsonModel
from src.users.domain.value_objects.display_name import (
    DISPLAY_NAME_MAX_LENGTH,
    DISPLAY_NAME_MIN_LENGTH,
)
from src.users.domain.value_objects.password import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
)
from src.users.domain.value_objects.username import (
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_PATTERN,
)


def _get_symbol_form(count: int, form_type: Literal["exact", "range"]) -> str:
    """Возвращает правильную форму слова "символ" для описания длины строки.

    Используется в генерации человекочитаемых описаний диапазонов длины
    в документации API.

    Поддерживаемые сценарии:
      - "exact": для фразы "ровно X символ(а/ов)";
      - "range": для фразы "от X до Y символ(а/ов)".

    Правила склонения соответствуют нормам русского языка для существительных
    мужского рода на -л: форма зависит от последней цифры с учётом
    исключений.

    Parameters
    ----------
    count : int
        Числовое значение, для которого определяется форма слова.
        Может быть отрицательным - используется абсолютное значение.
    form_type : Literal["exact", "range"]
        Тип фразы, для которой нужна форма:
          - "exact" - для точного значения ("ровно X");
          - "range" - для диапазона ("от X до Y").

    Returns
    -------
    str
        Одна из форм: "символ", "символа" или "символов".

    Raises
    ------
    ValueError
        Если передан неизвестный тип фразы.
    """
    last_digit = (abs_count := abs(count)) % 10
    last_two_digits = abs_count % 100

    match form_type:
        case "exact":
            if abs_count == 1:
                return "символ"

            if 2 <= last_digit <= 4 and last_two_digits not in (12, 13, 14):
                return "символа"
        case "range":
            if last_digit == 1 and last_two_digits != 11:
                return "символа"

    return "символов"


def _length_description(min_length: int, max_length: int) -> str:
    """Формирует текстовое описание диапазона длины строки для документации API.

    Parameters
    ----------
    min_length : int
        Минимально допустимое количество символов.
    max_length : int
        Максимально допустимое количество символов.

    Returns
    -------
    str
        Отформатированная строка:
          - "ровно {min} {форма}", если min_length == max_length;
          - "от {min} до {max} {форма}" - в остальных случаях.
        Форма слова "символ" подбирается автоматически с учётом правил
        склонения и типа фразы.

    Raises
    ------
    ValueError
        Если хотя бы один из параметров отрицательный.
        Если min_length > max_length.
    """
    if min_length < 0 or max_length < 0:
        errors = [
            f"min_length = {min_length}" if min_length < 0 else None,
            f"max_length = {max_length}" if max_length < 0 else None,
        ]

        raise ValueError(
            "Length cannot be negative number: " + ", ".join(filter(None, errors)) + "."
        )

    if min_length > max_length:
        raise ValueError("Min length cannot be larger than max length.")

    if min_length == max_length:
        return f"ровно {min_length} {_get_symbol_form(min_length, 'exact')}"

    return f"от {min_length} до {max_length} {_get_symbol_form(max_length, 'range')}"


class RegisterUserRequest(BaseJsonModel):
    """Схема запроса регистрации.

    Attributes
    ----------
    username : str
        Строковое представление логина пользователя.
    password : str
        Строковое представление пароля пользователя.
    display_name : str
        Строковое представление отображаемого имени пользователя.

    Notes
    -----
    Для логина пользователя (username) и отображаемого имени пользователя (display_name)
    ведущие и завершающие пробельные символы удаляются перед обработкой.

    See Also
    --------
    :class:`BaseJsonModel`
        Базовая модель данных, сериализуемых в JSON.
    """

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
            "Логин пользователя ("
            + f"{_length_description(USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH)}, "
            + "латинские строчные и заглавные, цифры, дефис и нижнее подчёркивание"
            + ")."
        ),
        examples=["john_doe", "user123", "ThisIsNotAUsername"],
    )
    password: Annotated[
        str,
        StringConstraints(
            min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
        ),
    ] = Field(
        description=(
            "Пароль ("
            + f"{_length_description(PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH)}, "
            + "любые символы в соответствии с NIST SP 800-63B"
            + ")."
        ),
        examples=["НадёжныйP@ssword123!"],
        json_schema_extra={"sensitive": True},
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
                _length_description(DISPLAY_NAME_MIN_LENGTH, DISPLAY_NAME_MAX_LENGTH)
            }, "
            + "любые Unicode-символы"
            + ")."
        ),
        examples=["Александр", "7", "一只非常重要的鸡", "🍆"],
    )
