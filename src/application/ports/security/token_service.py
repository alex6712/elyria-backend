from typing import Protocol
from uuid import UUID


class TokenService(Protocol):
    """Порт сервиса управления токенами.

    Определяет контракт для создания и проверки access-токенов,
    а также для генерации и хеширования refresh-токенов.

    Access-токен является короткоживущим JWT, подписанным ключом
    Ed25519. Refresh-токен является длинным случайным токеном,
    хеш которого хранится в базе данных.

    Notes
    -----
    Порт не зависит от конкретного формата токенов или алгоритма
    подписи. Выбор технологии является ответственностью
    Infrastructure Layer.
    """

    async def create_access_token(self, user_id: UUID) -> str:
        """Создаёт access-токен для указанного пользователя.

        Parameters
        ----------
        user_id : UUID
            Идентификатор пользователя, для которого создаётся токен.

        Returns
        -------
        str
            Сформированный access-токен.

        Raises
        ------
        TokenCreationError
            Если не удалось создать токен.
        """
        ...

    async def decode_access_token(self, token: str) -> dict:
        """Проверяет и декодирует access-токен.

        Parameters
        ----------
        token : str
            Access-токен для проверки.

        Returns
        -------
        dict
            Содержимое payload токена.

        Raises
        ------
        InvalidTokenError
            Если токен недействителен, просрочен или имеет
            некорректную подпись.
        """
        ...

    async def create_refresh_token(self) -> str:
        """Генерирует новый refresh-токен.

        Returns
        -------
        str
            Сгенерированный refresh-токен.
        """
        ...

    async def hash_refresh_token(self, token: str) -> str:
        """Вычисляет хеш refresh-токена.

        Parameters
        ----------
        token : str
            Refresh-токен в открытом виде.

        Returns
        -------
        str
            Хеш refresh-токена.

        Notes
        -----
        Хеширование выполняется с использованием HMAC-SHA256
        и секретного ключа из конфигурации приложения.
        """
        ...
