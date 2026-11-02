"""Unit-тесты ``SqlAlchemyIdentityRepository``."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from src.shared.domain.exceptions import ConcurrentModificationError
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


class TestSqlAlchemyIdentityRepositoryGetByEmail:
    """Метод ``get_by_email`` репозитория ``Identity``."""

    async def test_returns_identity_when_found(self) -> None:
        connection = AsyncMock()
        repo = SqlAlchemyIdentityRepository(connection)
        result_mock = MagicMock()
        result_mock.mappings.return_value.first.return_value = _mock_row(
            id="123e4567-e89b-12d3-a456-426614174000",
        )
        connection.execute = AsyncMock(return_value=result_mock)

        identity = await repo.get_by_email(Email("john@example.com"))

        assert identity is not None
        assert identity.email.value == "john@example.com"

    async def test_uses_lowercase_email_in_where(self) -> None:
        connection = AsyncMock()
        repo = SqlAlchemyIdentityRepository(connection)
        result_mock = MagicMock()
        result_mock.mappings.return_value.first.return_value = None
        connection.execute = AsyncMock(return_value=result_mock)

        identity = await repo.get_by_email(Email("john@example.com"))

        assert identity is None
        select_stmt = connection.execute.call_args.args[0]
        assert "lower(identities.email)" in str(select_stmt)
        assert "john@example.com" in select_stmt.compile().params.values()


class TestSqlAlchemyIdentityRepositorySaveVerification:
    """Метод ``save_verification`` репозитория ``Identity``."""

    async def test_successful_save_increments_version(self) -> None:
        connection = AsyncMock()
        repo = SqlAlchemyIdentityRepository(connection)
        identity = _make_identity()
        identity.verify_email()
        result_mock = MagicMock()
        result_mock.rowcount = 1
        connection.execute = AsyncMock(return_value=result_mock)

        await repo.save_verification(identity)

        update_stmt = connection.execute.call_args.args[0]
        params = update_stmt.compile().params
        assert params["email_verified"] is True
        assert identity.version == 2

    async def test_stale_version_raises_error(self) -> None:
        connection = AsyncMock()
        repo = SqlAlchemyIdentityRepository(connection)
        identity = _make_identity()
        identity.verify_email()
        result_mock = MagicMock()
        result_mock.rowcount = 0
        connection.execute = AsyncMock(return_value=result_mock)

        with pytest.raises(ConcurrentModificationError):
            await repo.save_verification(identity)
