from typing import Protocol, runtime_checkable

from src.users.domain.value_objects import Password


@runtime_checkable
class CompromisedPasswordChecker(Protocol):
    """Порт сервиса проверки пароля на утечку данных.

    Определяет контракт для проверки, входит ли пароль в список
    паролей, известных по утечкам данных.

    Notes
    -----
    Порт оперирует исключительно прикладным языком: метод
    возвращает ``bool`` и не раскрывает детали работы сервиса.
    """

    async def is_compromised(self, password: Password) -> bool:
        """Проверить, является ли пароль скомпрометированным.

        Parameters
        ----------
        password : Password
            Пароль в виде объект-значения для проверки.

        Returns
        -------
        bool
            ``True``, если пароль встречается в известных утечках
            данных, иначе ``False``.
        """
        ...
