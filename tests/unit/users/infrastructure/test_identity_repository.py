"""Unit-тесты ``SqlAlchemyIdentityRepository``."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from src.users.domain.entities import Identity
from src.users.domain.exceptions import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from src.users.domain.value_objects import Email, Username
from src.users.infrastructure.adapters.persistence import (
    SqlAlchemyIdentityRepository,
)


def _make_identity(
    *,
    username: str = "john_doe",
    email: str = "john@example.com",
) -> Identity:
    return Identity.register(
        username=Username(username),
        password_hash="hash:secret",
        email=Email(email),
    )


def _mock_row(
    *,
    id: str | None = None,
    username: str = "john_doe",
    email: str = "john@example.com",
    email_verified: bool = False,
    password_hash: str = "hash:secret",
    is_active: bool = True,
    version: int = 1,
) -> dict[str, object]:
    return {
        "id": id,
        "username": username,
        "email": email,
        "email_verified": email_verified,
        "password_hash": password_hash,
        "is_active": is_active,
        "version": version,
        "created_at": None,
        "updated_at": None,
    }


class TestSqlAlchemyIdentityRepositoryAdd:
    """Метод ``add`` репозитория ``Identity``."""

    async def test_successful_add(self) -> None:
        connection = AsyncMock()
        repo = SqlAlchemyIdentityRepository(connection)
        identity = _make_identity()

        await repo.add(identity)

        connection.execute.assert_awaited_once()
        insert_stmt = connection.execute.call_args.args[0]
        params = insert_stmt.compile().params
        assert params["email"] == "john@example.com"
        assert params["email_verified"] is False

    async def test_duplicate_username_raises_error(self) -> None:
        connection = AsyncMock()
        repo = SqlAlchemyIdentityRepository(connection)
        identity = _make_identity()

        err = IntegrityError("INSERT", (), Exception("uq_identities_username"))
        connection.execute = AsyncMock(side_effect=err)

        with pytest.raises(UsernameAlreadyExistsError, match="username"):
            await repo.add(identity)

    async def test_duplicate_email_raises_error(self) -> None:
        connection = AsyncMock()
        repo = SqlAlchemyIdentityRepository(connection)
        identity = _make_identity()

        err = IntegrityError("INSERT", (), Exception("uq_identities_email_lower"))
        connection.execute = AsyncMock(side_effect=err)

        with pytest.raises(EmailAlreadyExistsError, match="email"):
            await repo.add(identity)

    async def test_unrelated_integrity_error_propagates(self) -> None:
        connection = AsyncMock()
        repo = SqlAlchemyIdentityRepository(connection)
        identity = _make_identity()

        err = IntegrityError("INSERT", (), Exception("some_other_constraint"))
        connection.execute = AsyncMock(side_effect=err)

        with pytest.raises(IntegrityError):
            await repo.add(identity)


class TestSqlAlchemyIdentityRepositoryGetMapping:
    """Маппинг строк ``_row_to_identity``."""

    async def test_row_maps_email_and_email_verified(self) -> None:
        connection = AsyncMock()
        repo = SqlAlchemyIdentityRepository(connection)

        row = _mock_row(
            id="123e4567-e89b-12d3-a456-426614174000",
            email="alice@test.com",
            email_verified=True,
            version=3,
        )
        result_mock = MagicMock()
        result_mock.mappings.return_value.first.return_value = row
        connection.execute = AsyncMock(return_value=result_mock)

        identity = await repo.get_by_username(Username("john_doe"))

        assert identity is not None
        assert identity.email.value == "alice@test.com"
        assert identity.email_verified is True
        assert identity.version == 3
