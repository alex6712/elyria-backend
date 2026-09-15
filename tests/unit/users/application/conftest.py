"""Фикстуры для unit-тестов Application Layer."""

from tests.fakes.identity_uow import FakeUsersUnitOfWork
from tests.fakes.security import (
    FakeCompromisedPasswordChecker,
    FakePasswordHasher,
    FakeTokenHasher,
    FakeTokenIssuer,
)

ACCESS_TOKEN_LIFETIME_MINUTES = 15
REFRESH_TOKEN_LIFETIME_DAYS = 30


def make_uow() -> FakeUsersUnitOfWork:
    """Создать ``FakeUsersUnitOfWork``."""
    return FakeUsersUnitOfWork()


def make_password_hasher() -> FakePasswordHasher:
    """Создать ``FakePasswordHasher``."""
    return FakePasswordHasher()


def make_token_issuer() -> FakeTokenIssuer:
    """Создать ``FakeTokenIssuer``."""
    return FakeTokenIssuer()


def make_token_hasher() -> FakeTokenHasher:
    """Создать ``FakeTokenHasher``."""
    return FakeTokenHasher()


def make_compromised_checker() -> FakeCompromisedPasswordChecker:
    """Создать ``FakeCompromisedPasswordChecker``."""
    return FakeCompromisedPasswordChecker()
