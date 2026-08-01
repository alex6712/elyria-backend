import hashlib
import hmac


class HmacSha256TokenHasher:
    """Реализация :class:`TokenHasher` на основе HMAC-SHA256.

    Использует секретный ключ и алгоритм HMAC с SHA-256 для получения
    детерминированного криптографического хеша токена.

    Такой подход позволяет безопасно хранить хеши токенов (например,
    refresh-токенов) и сравнивать их без сохранения исходных значений.

    Parameters
    ----------
    secret_key : bytes
        Секретный ключ, используемый алгоритмом HMAC.
    """

    def __init__(self, secret_key: bytes) -> None:
        self._secret_key = secret_key

    def hash(self, token_str: str) -> str:
        """Вычислить HMAC-SHA256 хеш токена.

        Parameters
        ----------
        token_str : str
            Исходная строка токена.

        Returns
        -------
        str
            Шестнадцатеричное представление HMAC-SHA256 хеша.
        """
        return hmac.new(
            self._secret_key, token_str.encode("utf-8"), hashlib.sha256
        ).hexdigest()
