"""Фикстуры для unit-тестов Application Layer."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from src.identity.application.dto import TokenClaimsDTO
from tests.fakes.identity_uow import FakeIdentityUnitOfWork
from tests.fakes.security import (
    FakePasswordHasher,
    FakeTokenBlacklist,
    FakeTokenHasher,
    FakeTokenIssuer,
    FakeTokenVerifier,
)

ACCESS_TOKEN_LIFETIME_MINUTES = 15
REFRESH_TOKEN_LIFETIME_DAYS = 30


@pytest.fixture
def uow() -> FakeIdentityUnitOfWork:
    """Фейк единицы работы с репозиториями в памяти."""
    return FakeIdentityUnitOfWork()


@pytest.fixture
def password_hasher() -> FakePasswordHasher:
    """Фейк хеширования паролей."""
    return FakePasswordHasher()


@pytest.fixture
def token_issuer() -> FakeTokenIssuer:
    """Фейк выпуска токенов."""
    return FakeTokenIssuer()


@pytest.fixture
def token_verifier() -> FakeTokenVerifier:
    """Фейк проверки токенов."""
    return FakeTokenVerifier()


@pytest.fixture
def token_hasher() -> FakeTokenHasher:
    """Фейк хеширования токенов."""
    return FakeTokenHasher()


@pytest.fixture
def token_blacklist() -> FakeTokenBlacklist:
    """Фейк чёрного списка токенов."""
    return FakeTokenBlacklist()


@pytest.fixture
def at_lifetime_minutes() -> int:
    """Время жизни access-токена для тестов."""
    return ACCESS_TOKEN_LIFETIME_MINUTES


@pytest.fixture
def rt_lifetime_days() -> int:
    """Время жизни refresh-токена для тестов."""
    return REFRESH_TOKEN_LIFETIME_DAYS


def assert_claims_issued_within(
    claims_expires_at: datetime,
    issued_at: datetime,
    lifetime: timedelta,
    *,
    before: datetime,
    after: datetime,
) -> None:
    """Проверить, что срок жизни утверждений вычислен в интервале теста.

    Parameters
    ----------
    claims_expires_at : datetime
        Момент истечения из утверждений токена.
    issued_at : datetime
        Момент выпуска из утверждений токена.
    lifetime : timedelta
        Ожидаемое время жизни токена.
    before : datetime
        Момент начала выполнения сценария.
    after : datetime
        Момент завершения выполнения сценария.
    """
    assert before <= issued_at <= after
    assert claims_expires_at == issued_at + lifetime


def make_claims(
    *,
    user_id: UUID,
    session_id: UUID,
    token_id: UUID,
    expires_at: datetime | None = None,
    issued_at: datetime | None = None,
) -> TokenClaimsDTO:
    """Создать утверждения токена для фейка верификатора."""
    issued_at = issued_at or datetime.now(UTC)
    expires_at = expires_at or issued_at + timedelta(minutes=15)

    return TokenClaimsDTO(
        user_id=user_id,
        expires_at=expires_at,
        issued_at=issued_at,
        token_id=token_id,
        session_id=session_id,
    )
