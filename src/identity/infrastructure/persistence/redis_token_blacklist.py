from datetime import UTC, datetime
from math import ceil
from uuid import UUID

from redis.asyncio import Redis as AsyncRedis


class RedisTokenBlacklist:
    """Реализация порта ``TokenBlacklist`` для хранения отозванных токенов в Redis.

    Parameters
    ----------
    client : AsyncRedis
        Асинхронный клиент Redis.
    """

    def __init__(self, client: AsyncRedis) -> None:
        self._client = client

    @staticmethod
    def _build_blacklist_key(token_id: UUID) -> str:
        """Формирует ключ для хранения информации об отозванном токене.

        Parameters
        ----------
        token_id : UUID
            Уникальный идентификатор токена.

        Returns
        -------
        str
            Redis-ключ вида:
            "blacklist:access-token:{token_id}"
        """
        return f"blacklist:access-token:{token_id}"

    async def revoke(self, token_id: UUID, expires_at: datetime) -> None:
        """Помещает токен в черный список до момента его планового истечения.

        Если время жизни токена уже вышло или равно нулю,
        операция пропускается без записи в Redis.

        Parameters
        ----------
        token_id : UUID
            Уникальный идентификатор отзываемого токена.
        expires_at : datetime
            Плановое время истечения срока действия токена.
            Наивное значение интерпретируется как UTC.
        """
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        ttl_delta = expires_at - datetime.now(UTC)
        ttl_seconds = ceil(ttl_delta.total_seconds())

        if ttl_seconds <= 0:
            return

        _ = await self._client.set(
            self._build_blacklist_key(token_id), "1", ex=ttl_seconds
        )

    async def is_revoked(self, token_id: UUID) -> bool:
        """Проверяет наличие токена в черном списке.

        Parameters
        ----------
        token_id : UUID
            Уникальный идентификатор проверяемого токена.

        Returns
        -------
        bool
            ``True`` - если токен найден в черном списке,
            иначе ``False``.
        """
        return bool(await self._client.exists(self._build_blacklist_key(token_id)))
