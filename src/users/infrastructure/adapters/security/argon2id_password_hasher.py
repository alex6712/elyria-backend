from pwdlib import PasswordHash

from src.users.domain.value_objects import Password


class Argon2idPasswordHasher:
    """Реализация порта ``PasswordHasher`` с использованием Argon2id.

    Использует библиотеку pwdlib с хеш-схемой Argon2id для
    хеширования и проверки паролей.

    Notes
    -----
    Параметры Argon2id используются по умолчанию, предоставляемые
    pwdlib. При необходимости могут быть переопределены через
    конфигурацию приложения.
    """

    _password_hash = PasswordHash.recommended()

    def hash(self, password: Password) -> str:
        """Вычисляет хеш пароля с использованием Argon2id.

        Parameters
        ----------
        password : Password
            Пароль в виде объект-значения для хеширования.

        Returns
        -------
        str
            Строковое представление хеша пароля.
        """
        return self._password_hash.hash(password.reveal())

    def verify(self, password: Password, hash: str) -> bool:
        """Проверяет соответствие пароля хешу Argon2id.

        Parameters
        ----------
        password : Password
            Пароль в виде объект-значения для проверки.
        hash : str
            Хеш, с которым требуется сравнить пароль.

        Returns
        -------
        bool
            ``True``, если пароль соответствует хешу, иначе ``False``.
        """
        return self._password_hash.verify(password.reveal(), hash)

    def verify_and_update(
        self, password: Password, hash: str
    ) -> tuple[bool, str | None]:
        """Проверяет соответствие пароля хешу и обновляет хеш
        при необходимости.

        Parameters
        ----------
        password : Password
            Пароль в виде объект-значения для проверки.
        hash : str
            Хеш, с которым требуется сравнить пароль.

        Returns
        -------
        tuple[bool, str | None]
            Кортеж из двух элементов:

            - ``True``, если пароль соответствует хешу, иначе ``False``.
            - Новый хеш, если алгоритм или параметры устарели,
              иначе ``None``.
        """
        return self._password_hash.verify_and_update(password.reveal(), hash)
