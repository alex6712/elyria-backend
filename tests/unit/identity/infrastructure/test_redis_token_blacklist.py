"""Unit-тесты RedisTokenBlacklist на фейковом клиенте Redis."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from src.identity.infrastructure.persistence.redis_token_blacklist import (
    RedisTokenBlacklist,
)


class FakeRedisClient:
    """Минимальная имитация AsyncRedis для проверки команд."""

    def __init__(self) -> None:
        self.storage: dict[str, tuple[str, int]] = {}
        self.set_calls: list[tuple[str, str, int]] = []
        self.exists_calls: list[str] = []

    async def set(self, key: str, value: str, ex: int) -> None:
        """Записать значение с TTL."""
        self.set_calls.append((key, value, ex))
        self.storage[key] = (value, ex)

    async def exists(self, key: str) -> int:
        """Вернуть 1, если ключ существует."""
        self.exists_calls.append(key)
        return 1 if key in self.storage else 0


class TestRedisTokenBlacklist:
    """Проверка работы с чёрным списком токенов."""

    async def test_revoke_sets_key_with_ttl(self) -> None:
        """Отзыв токена записывает ключ с TTL до истечения токена."""
        client = FakeRedisClient()
        blacklist = RedisTokenBlacklist(client)
        token_id = UUID("11111111-1111-1111-1111-111111111111")
        expires_at = datetime.now(UTC) + timedelta(hours=1)

        await blacklist.revoke(token_id, expires_at)

        key = f"blacklist:access-token:{token_id}"
        assert client.set_calls == [(key, "1", 3600)]

    async def test_revoke_naive_expires_at_treated_as_utc(self) -> None:
        """Наивное время истечения интерпретируется как UTC."""
        client = FakeRedisClient()
        blacklist = RedisTokenBlacklist(client)
        token_id = UUID("11111111-1111-1111-1111-111111111111")
        naive = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=30)

        await blacklist.revoke(token_id, naive)

        assert client.set_calls[0][0] == f"blacklist:access-token:{token_id}"
        assert client.set_calls[0][2] == 1800

    async def test_revoke_expired_token_skips_write(self) -> None:
        """Токен с истёкшим сроком не записывается в Redis."""
        client = FakeRedisClient()
        blacklist = RedisTokenBlacklist(client)
        token_id = UUID("11111111-1111-1111-1111-111111111111")
        expires_at = datetime.now(UTC) - timedelta(minutes=5)

        await blacklist.revoke(token_id, expires_at)

        assert client.set_calls == []

    async def test_revoke_zero_ttl_skips_write(self) -> None:
        """Нулевой TTL пропускает запись."""
        client = FakeRedisClient()
        blacklist = RedisTokenBlacklist(client)
        token_id = UUID("11111111-1111-1111-1111-111111111111")

        await blacklist.revoke(token_id, datetime.now(UTC))

        assert client.set_calls == []

    async def test_is_revoked_true_for_blacklisted(self) -> None:
        """Занесённый в чёрный список токен определяется как отозванный."""
        client = FakeRedisClient()
        blacklist = RedisTokenBlacklist(client)
        token_id = UUID("11111111-1111-1111-1111-111111111111")
        client.storage[f"blacklist:access-token:{token_id}"] = ("1", 60)

        assert await blacklist.is_revoked(token_id) is True

    async def test_is_revoked_false_for_unknown(self) -> None:
        """Неизвестный токен не считается отозванным."""
        client = FakeRedisClient()
        blacklist = RedisTokenBlacklist(client)
        token_id = UUID("11111111-1111-1111-1111-111111111111")

        assert await blacklist.is_revoked(token_id) is False

    async def test_is_revoked_uses_expected_key(self) -> None:
        """Проверка использует ключ вида ``blacklist:access-token:{id}``."""
        client = FakeRedisClient()
        blacklist = RedisTokenBlacklist(client)
        token_id = UUID("11111111-1111-1111-1111-111111111111")

        await blacklist.is_revoked(token_id)

        assert client.exists_calls == [f"blacklist:access-token:{token_id}"]
