from passlib.context import CryptContext


class Argon2PasswordHasher:
    """Реализация порта ``PasswordHasher`` с использованием Argon2id.

    Использует библиотеку Passlib с хеш-схемой Argon2id для
    хеширования и проверки паролей.

    Notes
    -----
    Параметры Argon2id используются по умолчанию, предоставляемые
    Passlib. При необходимости могут быть переопределены через
    конфигурацию приложения.
    """

    _context = CryptContext(schemes=["argon2"], deprecated="auto")

    def hash(self, password: str) -> str:
        """Вычисляет хеш пароля с использованием Argon2id.

        Parameters
        ----------
        password : str
            Пароль в открытом виде для хеширования.

        Returns
        -------
        str
            Строковое представление хеша пароля в формате Passlib.
        """
        return self._context.hash(password)

    def verify(self, password: str, hash: str) -> bool:
        """Проверяет соответствие пароля хешу Argon2id.

        Parameters
        ----------
        password : str
            Пароль в открытом виде для проверки.
        hash : str
            Хеш в формате Passlib для сравнения.

        Returns
        -------
        bool
            ``True``, если пароль соответствует хешу, иначе ``False``.
        """
        return self._context.verify(password, hash)
