"""Unit-тесты ``RedisRateLimiter``."""

import hashlib
import hmac
from datetime import timedelta
from typing import cast

import pytest
from redis.asyncio import Redis as AsyncRedis

from src.shared.application.exceptions import InvalidRateLimitParametersError
from src.shared.infrastructure.adapters.persistence import RedisRateLimiter
from tests.fakes.redis import FakeRedisClient

_LIMIT = 5
_WINDOW_SECONDS = 3600

_KEY_SECRET = b"test-rate-limit-key-secret"
"""Секрет подписи идентификаторов счётчиков в тестах."""

_OTHER_KEY_SECRET = b"another-rate-limit-key-secret"
"""Отличный секрет для проверки зависимости ключа от секрета."""


def _digest(subject: str, *, secret: bytes = _KEY_SECRET) -> str:
    """Вычислить ожидаемую подпись источника запроса."""
    return hmac.new(secret, subject.strip().encode("utf-8"), hashlib.sha256).hexdigest()


def _make_limiter() -> tuple[RedisRateLimiter, FakeRedisClient]:
    """Создать ограничитель на фейковом клиенте Redis."""
    client = FakeRedisClient()
    limiter = RedisRateLimiter(cast(AsyncRedis, client), key_secret=_KEY_SECRET)
    return limiter, client


class TestRedisRateLimiterKeyFormat:
    """Формат ключа счётчика."""

    async def test_key_is_namespaced_and_starts_with_operation(self) -> None:
        client = FakeRedisClient()
        limiter = RedisRateLimiter(cast(AsyncRedis, client), key_secret=_KEY_SECRET)

        _ = await limiter.acquire(
            "email-verify", "1.2.3.4", limit=_LIMIT, window_seconds=_WINDOW_SECONDS
        )

        assert client.keys() == {f"rate-limit:email-verify:{_digest('1.2.3.4')}"}

    async def test_subject_is_not_stored_in_plain_text(self) -> None:
        client = FakeRedisClient()
        limiter = RedisRateLimiter(cast(AsyncRedis, client), key_secret=_KEY_SECRET)

        _ = await limiter.acquire(
            "email-verify",
            "user@example.com",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )

        key = next(iter(client.keys()))
        assert "user@example.com" not in key
        assert "@" not in key

    async def test_subject_is_signed_not_plain_hashed(self) -> None:
        client = FakeRedisClient()
        limiter = RedisRateLimiter(cast(AsyncRedis, client), key_secret=_KEY_SECRET)

        _ = await limiter.acquire(
            "email-verify",
            "user@example.com",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )

        key = next(iter(client.keys()))
        plain_sha256 = hashlib.sha256(b"user@example.com").hexdigest()
        assert plain_sha256 not in key
        assert _digest("user@example.com") in key

    async def test_key_depends_on_secret(self) -> None:
        client = FakeRedisClient()
        limiter = RedisRateLimiter(
            cast(AsyncRedis, client), key_secret=_OTHER_KEY_SECRET
        )

        _ = await limiter.acquire(
            "email-verify", "1.2.3.4", limit=_LIMIT, window_seconds=_WINDOW_SECONDS
        )

        assert client.keys() == {
            f"rate-limit:email-verify:{_digest('1.2.3.4', secret=_OTHER_KEY_SECRET)}"
        }

    async def test_key_depends_on_operation(self) -> None:
        client = FakeRedisClient()
        limiter = RedisRateLimiter(cast(AsyncRedis, client), key_secret=_KEY_SECRET)

        _ = await limiter.acquire(
            "email-verify", "1.2.3.4", limit=_LIMIT, window_seconds=_WINDOW_SECONDS
        )
        _ = await limiter.acquire(
            "login", "1.2.3.4", limit=_LIMIT, window_seconds=_WINDOW_SECONDS
        )

        assert client.keys() == {
            f"rate-limit:email-verify:{_digest('1.2.3.4')}",
            f"rate-limit:login:{_digest('1.2.3.4')}",
        }

    async def test_operation_is_trimmed(self) -> None:
        client = FakeRedisClient()
        limiter = RedisRateLimiter(cast(AsyncRedis, client), key_secret=_KEY_SECRET)

        _ = await limiter.acquire(
            "  email-verify  ",
            "1.2.3.4",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )

        assert client.keys() == {f"rate-limit:email-verify:{_digest('1.2.3.4')}"}

    async def test_trimmed_subject_shares_counter_with_untrimmed(self) -> None:
        limiter, _ = _make_limiter()

        for _ in range(_LIMIT):
            _ = await limiter.acquire(
                "email-verify", "1.1.1.1", limit=_LIMIT, window_seconds=_WINDOW_SECONDS
            )

        decision = await limiter.acquire(
            "email-verify", "  1.1.1.1  ", limit=_LIMIT, window_seconds=_WINDOW_SECONDS
        )

        assert decision.allowed is False

    @pytest.mark.parametrize("subject", ["", "   ", "\t\n"])
    async def test_rejects_blank_subject(self, subject: str) -> None:
        limiter, _ = _make_limiter()

        with pytest.raises(InvalidRateLimitParametersError):
            _ = await limiter.acquire(
                "email-verify",
                subject,
                limit=_LIMIT,
                window_seconds=_WINDOW_SECONDS,
            )

    @pytest.mark.parametrize(
        "operation",
        ["", "   ", "Email Verify", "email verify", "email:verify", "email/verify"],
    )
    async def test_rejects_malformed_operation(self, operation: str) -> None:
        limiter, _ = _make_limiter()

        with pytest.raises(InvalidRateLimitParametersError):
            _ = await limiter.acquire(
                operation,
                "1.2.3.4",
                limit=_LIMIT,
                window_seconds=_WINDOW_SECONDS,
            )


class TestRedisRateLimiterAcquireAllowed:
    """Поведение в пределах лимита."""

    async def test_first_request_allowed(self) -> None:
        limiter, _ = _make_limiter()

        decision = await limiter.acquire(
            "email-verify",
            "subject@example.com",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )

        assert decision.allowed is True

    async def test_reports_configured_limit(self) -> None:
        limiter, _ = _make_limiter()

        decision = await limiter.acquire(
            "email-verify",
            "subject@example.com",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )

        assert decision.limit == _LIMIT

    async def test_remaining_decreases(self) -> None:
        limiter, _ = _make_limiter()

        first = await limiter.acquire(
            "email-verify",
            "subject@example.com",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )
        second = await limiter.acquire(
            "email-verify",
            "subject@example.com",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )

        assert first.remaining == _LIMIT - 1
        assert second.remaining == _LIMIT - 2

    async def test_retry_after_is_zero_when_allowed(self) -> None:
        limiter, _ = _make_limiter()

        decision = await limiter.acquire(
            "email-verify",
            "subject@example.com",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )

        assert decision.retry_after == 0

    async def test_reset_after_matches_window(self) -> None:
        limiter, _ = _make_limiter()

        decision = await limiter.acquire(
            "email-verify",
            "subject@example.com",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )

        assert decision.reset_after == _WINDOW_SECONDS

    async def test_requests_below_limit_are_allowed(self) -> None:
        limiter, _ = _make_limiter()

        decisions = [
            await limiter.acquire(
                "email-verify",
                "subject@example.com",
                limit=_LIMIT,
                window_seconds=_WINDOW_SECONDS,
            )
            for _ in range(_LIMIT)
        ]

        assert all(d.allowed for d in decisions)


class TestRedisRateLimiterAcquireExceeded:
    """Поведение при исчерпании лимита."""

    async def test_request_over_limit_is_denied(self) -> None:
        limiter, _ = _make_limiter()

        for _ in range(_LIMIT):
            _ = await limiter.acquire(
                "email-verify",
                "subject@example.com",
                limit=_LIMIT,
                window_seconds=_WINDOW_SECONDS,
            )

        decision = await limiter.acquire(
            "email-verify",
            "subject@example.com",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )

        assert decision.allowed is False

    async def test_remaining_is_zero_when_denied(self) -> None:
        limiter, _ = _make_limiter()
        decisions = [
            await limiter.acquire(
                "email-verify",
                "subject@example.com",
                limit=_LIMIT,
                window_seconds=_WINDOW_SECONDS,
            )
            for _ in range(_LIMIT + 1)
        ]

        assert decisions[-1].remaining == 0

    async def test_retry_after_is_positive_when_denied(self) -> None:
        limiter, _ = _make_limiter()
        decisions = [
            await limiter.acquire(
                "email-verify",
                "subject@example.com",
                limit=_LIMIT,
                window_seconds=_WINDOW_SECONDS,
            )
            for _ in range(_LIMIT + 1)
        ]

        assert decisions[-1].retry_after > 0

    async def test_retry_after_decreases_over_window(self) -> None:
        limiter, client = _make_limiter()

        for _ in range(_LIMIT + 1):
            _ = await limiter.acquire(
                "email-verify",
                "subject@example.com",
                limit=_LIMIT,
                window_seconds=_WINDOW_SECONDS,
            )

        client.advance(timedelta(seconds=1800))
        decision = await limiter.acquire(
            "email-verify",
            "subject@example.com",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )

        assert decision.retry_after == _WINDOW_SECONDS - 1800


class TestRedisRateLimiterWindow:
    """Поведение неподвижного окна."""

    async def test_window_resets_after_expiry(self) -> None:
        limiter, client = _make_limiter()

        for _ in range(_LIMIT + 1):
            _ = await limiter.acquire(
                "email-verify",
                "subject@example.com",
                limit=_LIMIT,
                window_seconds=_WINDOW_SECONDS,
            )

        client.advance(timedelta(seconds=_WINDOW_SECONDS))
        decision = await limiter.acquire(
            "email-verify",
            "subject@example.com",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )

        assert decision.allowed is True

    async def test_window_is_not_extended_by_activity(self) -> None:
        limiter, client = _make_limiter()

        _ = await limiter.acquire(
            "email-verify",
            "subject@example.com",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )
        client.advance(timedelta(seconds=1800))
        decision = await limiter.acquire(
            "email-verify",
            "subject@example.com",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )

        assert decision.reset_after == _WINDOW_SECONDS - 1800

    async def test_counter_starts_from_one_in_new_window(self) -> None:
        limiter, client = _make_limiter()

        _ = await limiter.acquire(
            "email-verify",
            "subject@example.com",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )
        client.advance(timedelta(seconds=_WINDOW_SECONDS))

        decision = await limiter.acquire(
            "email-verify",
            "subject@example.com",
            limit=_LIMIT,
            window_seconds=_WINDOW_SECONDS,
        )

        assert decision.remaining == _LIMIT - 1


class TestRedisRateLimiterKeyIsolation:
    """Изоляция счётчиков разных ключей."""

    async def test_keys_do_not_interfere(self) -> None:
        limiter, _ = _make_limiter()

        for _ in range(_LIMIT + 1):
            _ = await limiter.acquire(
                "email-verify", "1.1.1.1", limit=_LIMIT, window_seconds=_WINDOW_SECONDS
            )

        decision = await limiter.acquire(
            "email-verify", "2.2.2.2", limit=_LIMIT, window_seconds=_WINDOW_SECONDS
        )

        assert decision.allowed is True

    async def test_same_key_shares_counter(self) -> None:
        limiter, _ = _make_limiter()

        for _ in range(_LIMIT):
            _ = await limiter.acquire(
                "email-verify", "1.1.1.1", limit=_LIMIT, window_seconds=_WINDOW_SECONDS
            )

        decision = await limiter.acquire(
            "email-verify", "1.1.1.1", limit=_LIMIT, window_seconds=_WINDOW_SECONDS
        )

        assert decision.allowed is False


class TestRedisRateLimiterInvalidParameters:
    """Проверка аргументов ограничения."""

    @pytest.mark.parametrize("limit", [0, -1])
    async def test_rejects_non_positive_limit(self, limit: int) -> None:
        limiter, _ = _make_limiter()

        with pytest.raises(InvalidRateLimitParametersError):
            _ = await limiter.acquire(
                "email-verify",
                "subject@example.com",
                limit=limit,
                window_seconds=_WINDOW_SECONDS,
            )

    @pytest.mark.parametrize("window", [0, -1])
    async def test_rejects_non_positive_window(self, window: int) -> None:
        limiter, _ = _make_limiter()

        with pytest.raises(InvalidRateLimitParametersError):
            _ = await limiter.acquire(
                "email-verify",
                "subject@example.com",
                limit=_LIMIT,
                window_seconds=window,
            )


class TestRedisRateLimiterLimitOne:
    """Поведение при единичном лимите."""

    async def test_single_request_then_denied(self) -> None:
        limiter, _ = _make_limiter()

        first = await limiter.acquire(
            "email-verify",
            "subject@example.com",
            limit=1,
            window_seconds=_WINDOW_SECONDS,
        )
        second = await limiter.acquire(
            "email-verify",
            "subject@example.com",
            limit=1,
            window_seconds=_WINDOW_SECONDS,
        )

        assert first.allowed is True
        assert second.allowed is False
