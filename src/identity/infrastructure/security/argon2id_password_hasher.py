from pwdlib import PasswordHash


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

    def hash(self, password: str) -> str:
        """Вычисляет хеш пароля с использованием Argon2id.

        Parameters
        ----------
        password : str
            Пароль в открытом виде для хеширования.

        Returns
        -------
        str
            Строковое представление хеша пароля.
        """
        return self._password_hash.hash(password)

    def verify(self, password: str, hash: str) -> bool:
        """Проверяет соответствие пароля хешу Argon2id.

        Parameters
        ----------
        password : str
            Пароль в открытом виде для проверки.
        hash : str
            Хеш, с которым требуется сравнить пароль.

        Returns
        -------
        bool
            ``True``, если пароль соответствует хешу, иначе ``False``.
        """
        return self._password_hash.verify(password, hash)

    def verify_and_update(self, password: str, hash: str) -> tuple[bool, str | None]:
        """Проверяет соответствие пароля хешу и обновляет хеш
        при необходимости.

        Parameters
        ----------
        password : str
            Пароль в открытом виде для проверки.
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
        return self._password_hash.verify_and_update(password, hash)
