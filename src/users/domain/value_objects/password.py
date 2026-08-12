import unicodedata
from dataclasses import dataclass
from typing import override

from src.users.domain.exceptions import InvalidPasswordLengthError

PASSWORD_MIN_LENGTH = 15
"""Минимальная длина пароля (включительно)."""

PASSWORD_MAX_LENGTH = 128
"""Максимальная длина пароля (включительно)."""

_PASSWORD_MASK = "********"
"""Маска, подставляемая вместо пароля в строковых представлениях."""


@dataclass(init=False, repr=False, frozen=True, slots=True)
class Password:
    """Объект-значение, представляющий пароль пользователя.

    Основан на рекомендациях NIST SP 800-63B.

    Инкапсулирует строковое представление пароля в открытом виде
    и гарантирует соблюдение ограничений длины. Экземпляр класса
    всегда находится в корректном состоянии и может безопасно использоваться
    в доменных сущностях и сервисах.

    Parameters
    ----------
    value : str
        Пароль в открытом виде.

    Raises
    ------
    InvalidPasswordLengthError
        Если длина пароля выходит за допустимые пределы,
        установленные парольной политикой.

    Notes
    -----
    Пароль приводится к нормализованной форме Unicode (NFC) перед сохранением.
    Объект хранит пароль в открытом виде в памяти. Он не должен логироваться,
    сериализовываться в открытом виде или храниться дольше, чем это требуется
    для хеширования. Строковые представления (``__str__``, ``__repr__``)
    маскируют пароль; доступ к открытому значению - только через ``reveal()``.
    """

    _value: str

    def __init__(self, value: str) -> None:
        normalized = unicodedata.normalize("NFC", value)

        if not PASSWORD_MIN_LENGTH <= len(normalized) <= PASSWORD_MAX_LENGTH:
            raise InvalidPasswordLengthError(
                "Password must contain from "
                + f"{PASSWORD_MIN_LENGTH} to "
                + f"{PASSWORD_MAX_LENGTH} characters."
            )

        object.__setattr__(self, "_value", normalized)

    def reveal(self) -> str:
        """Раскрыть пароль в открытом виде.

        Returns
        -------
        str
            Пароль в открытом виде.

        Notes
        -----
        Единственный способ получить пароль в открытом виде.
        Вызывать только там, где пароль действительно необходим
        (например, при хешировании). Результат не должен
        логироваться или попадать в строковые представления.
        """
        return self._value

    @override
    def __str__(self) -> str:
        """Возвращает маску вместо пароля.

        Returns
        -------
        str
            Строка-маска, не содержащая пароль в открытом виде.

        Notes
        -----
        Метод намеренно не возвращает пароль: строковые
        представления объекта могут попадать в логи, трассировки
        и функции подстановки в строку. Для доступа к открытому
        значению используйте ``reveal()``.
        """
        return _PASSWORD_MASK

    @override
    def __repr__(self) -> str:
        """Возвращает строковое представление объекта без пароля.

        Returns
        -------
        str
            Строковое представление вида ``Password('********')``.

        Notes
        -----
        Пароль не включается в представление, чтобы исключить
        его попадание в логи и дампы объектов.
        """
        return f"Password({_PASSWORD_MASK!r})"
