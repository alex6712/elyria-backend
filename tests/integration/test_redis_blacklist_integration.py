"""Интеграционные тесты RedisTokenBlacklist на реальном Redis."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from redis.asyncio import Redis as AsyncRedis

from src.identity.infrastructure.persistence.redis_token_blacklist import (
    RedisTokenBlacklist,
)

pytestmark = pytest.mark.integration


class TestRedisTokenBlacklistIntegration:
    """Сквозная проверка чёрного списка токенов."""

    async def test_revoke_and_check(self, redis_client: AsyncRedis) -> None:
        """Отозванный токен определяется как отозванный."""
        blacklist = RedisTokenBlacklist(redis_client)
        token_id = uuid4()

        await blacklist.revoke(token_id, datetime.now(UTC) + timedelta(hours=1))

        assert await blacklist.is_revoked(token_id) is True

    async def test_unknown_token_not_revoked(self, redis_client: AsyncRedis) -> None:
        """Неотозванный токен не считается отозванным."""
        blacklist = RedisTokenBlacklist(redis_client)

        assert await blacklist.is_revoked(uuid4()) is False

    async def test_revoked_token_expires(self, redis_client: AsyncRedis) -> None:
        """После истечения TTL токен перестаёт быть отозванным."""
        blacklist = RedisTokenBlacklist(redis_client)
        token_id = uuid4()

        await blacklist.revoke(token_id, datetime.now(UTC) + timedelta(seconds=1))
        assert await blacklist.is_revoked(token_id) is True

        await asyncio.sleep(1.2)

        assert await blacklist.is_revoked(token_id) is False

    async def test_expired_token_not_written(self, redis_client: AsyncRedis) -> None:
        """Токен с истёкшим сроком не попадает в чёрный список."""
        blacklist = RedisTokenBlacklist(redis_client)
        token_id = uuid4()

        await blacklist.revoke(token_id, datetime.now(UTC) - timedelta(minutes=1))

        assert await blacklist.is_revoked(token_id) is False

    async def test_naive_expires_at_supported(self, redis_client: AsyncRedis) -> None:
        """Наивное время истечения интерпретируется как UTC."""
        blacklist = RedisTokenBlacklist(redis_client)
        token_id = uuid4()
        naive = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1)

        await blacklist.revoke(token_id, naive)

        assert await blacklist.is_revoked(token_id) is True
