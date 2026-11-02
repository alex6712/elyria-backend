"""Unit-тесты ``SqlAlchemyVerificationTokenRepository``."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from src.users.domain.entities import VerificationToken
from src.users.domain.value_objects import VerificationTokenPurpose
from src.users.infrastructure.adapters.persistence import (
    SqlAlchemyVerificationTokenRepository,
)

_IDENTITY_ID = UUID("123e4567-e89b-12d3-a456-426614174001")
_TOKEN_ID = UUID("123e4567-e89b-12d3-a456-426614174002")
_NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
_EXPIRES_AT = _NOW + timedelta(hours=1)


def _make_token() -> VerificationToken:
    return VerificationToken.issue(
        id=_TOKEN_ID,
        identity_id=_IDENTITY_ID,
        token_hash="hash:secret",
        purpose=VerificationTokenPurpose.EMAIL_VERIFICATION,
        expires_at=_EXPIRES_AT,
        now=_NOW,
    )


def _mock_row() -> dict[str, object]:
    return {
        "id": _TOKEN_ID,
        "identity_id": _IDENTITY_ID,
        "token_hash": "hash:secret",
        "purpose": VerificationTokenPurpose.EMAIL_VERIFICATION.value,
        "expires_at": _EXPIRES_AT,
        "used_at": None,
        "created_at": _NOW,
        "updated_at": None,
    }


class TestSqlAlchemyVerificationTokenRepositoryAdd:
    """Метод ``add`` репозитория ``VerificationToken``."""

    async def test_successful_add(self) -> None:
        connection = AsyncMock()
        repo = SqlAlchemyVerificationTokenRepository(connection)
        token = _make_token()

        await repo.add(token)

        connection.execute.assert_awaited_once()
        insert_stmt = connection.execute.call_args.args[0]
        params = insert_stmt.compile().params
        assert params["id"] == _TOKEN_ID
        assert params["identity_id"] == _IDENTITY_ID
        assert params["token_hash"] == "hash:secret"
        assert params["purpose"] == "email_verification"
        assert params["expires_at"] == _EXPIRES_AT
        assert params["used_at"] is None
        assert params["created_at"] == _NOW


class TestSqlAlchemyVerificationTokenRepositoryGetByTokenHash:
    """Метод ``get_by_token_hash`` репозитория ``VerificationToken``."""

    async def test_returns_token_when_found(self) -> None:
        connection = AsyncMock()
        repo = SqlAlchemyVerificationTokenRepository(connection)
        result_mock = MagicMock()
        result_mock.mappings.return_value.first.return_value = _mock_row()
        connection.execute = AsyncMock(return_value=result_mock)

        token = await repo.get_by_token_hash("hash:secret")

        assert token is not None
        assert token.id == _TOKEN_ID
        assert token.identity_id == _IDENTITY_ID
        assert token.purpose is VerificationTokenPurpose.EMAIL_VERIFICATION

        select_stmt = connection.execute.call_args.args[0]
        assert "hash:secret" in select_stmt.compile().params.values()

    async def test_returns_none_when_not_found(self) -> None:
        connection = AsyncMock()
        repo = SqlAlchemyVerificationTokenRepository(connection)
        result_mock = MagicMock()
        result_mock.mappings.return_value.first.return_value = None
        connection.execute = AsyncMock(return_value=result_mock)

        token = await repo.get_by_token_hash("missing")

        assert token is None


class TestSqlAlchemyVerificationTokenRepositoryInvalidate:
    """Метод ``invalidate_active_by_identity_id``."""

    async def test_update_sets_both_times_and_active_condition(self) -> None:
        connection = AsyncMock()
        repo = SqlAlchemyVerificationTokenRepository(connection)
        at = _NOW + timedelta(minutes=5)
        purpose = VerificationTokenPurpose.EMAIL_VERIFICATION

        await repo.invalidate_active_by_identity_id(
            _IDENTITY_ID,
            purpose,
            at=at,
        )

        update_stmt = connection.execute.call_args.args[0]
        sql = str(update_stmt)
        params = update_stmt.compile().params
        assert "used_at IS NULL" in sql
        assert params["used_at"] == at
        assert params["updated_at"] == at

    async def test_update_filters_by_identity_and_purpose(self) -> None:
        connection = AsyncMock()
        repo = SqlAlchemyVerificationTokenRepository(connection)
        purpose = VerificationTokenPurpose.EMAIL_VERIFICATION

        await repo.invalidate_active_by_identity_id(
            _IDENTITY_ID,
            purpose,
            at=_NOW,
        )

        update_stmt = connection.execute.call_args.args[0]
        sql = str(update_stmt)
        params = update_stmt.compile().params
        assert "identity_id = :identity_id_1" in sql
        assert "purpose = :purpose_1" in sql
        assert params["identity_id_1"] == _IDENTITY_ID
        assert params["purpose_1"] == purpose.value
