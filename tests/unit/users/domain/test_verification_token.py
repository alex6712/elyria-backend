"""Unit-тесты ``VerificationToken`` (domain entity)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.users.domain.entities import VerificationToken
from src.users.domain.exceptions import (
    InvalidVerificationTokenExpirationError,
    VerificationTokenAlreadyUsedError,
    VerificationTokenExpiredError,
)
from src.users.domain.value_objects import VerificationTokenPurpose

_NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)
"""Фиксированный момент времени, используемый в тестах."""

_DEFAULT_LIFETIME = timedelta(hours=24)
"""Стандартное время жизни токена подтверждения в тестах."""

_FAR_FUTURE_LIFETIME = timedelta(days=3650)
"""Время жизни, заведомо не истекающее на момент запуска тестов.

Используется в проверках, где момент сравнения не передаётся явно
и метод обращается к системному времени. Такие проверки не должны
зависеть от даты запуска: срок действия задаётся относительно
фиксированного ``_NOW``, поэтому берётся заведомо большой интервал.
"""


def _make_token(
    *,
    expires_in: timedelta = _DEFAULT_LIFETIME,
    used_at: datetime | None = None,
    purpose: VerificationTokenPurpose | None = None,
) -> VerificationToken:
    """Создать ``VerificationToken`` с указанными параметрами."""
    return VerificationToken(
        id=uuid4(),
        identity_id=uuid4(),
        token_hash="hashed:secret",
        purpose=purpose or VerificationTokenPurpose.EMAIL_VERIFICATION,
        expires_at=_NOW + expires_in,
        used_at=used_at,
        created_at=_NOW,
        updated_at=None,
    )


class TestVerificationTokenIssue:
    """Фабрика ``VerificationToken.issue``."""

    def test_sets_all_attributes(self) -> None:
        token_id = uuid4()
        identity_id = uuid4()
        expires_at = _NOW + timedelta(hours=24)

        token = VerificationToken.issue(
            id=token_id,
            identity_id=identity_id,
            token_hash="hashed:secret",
            purpose=VerificationTokenPurpose.EMAIL_VERIFICATION,
            expires_at=expires_at,
            now=_NOW,
        )

        assert token.id == token_id
        assert token.identity_id == identity_id
        assert token.token_hash == "hashed:secret"
        assert token.purpose is VerificationTokenPurpose.EMAIL_VERIFICATION
        assert token.expires_at == expires_at

    def test_used_at_is_none(self) -> None:
        token = VerificationToken.issue(
            id=uuid4(),
            identity_id=uuid4(),
            token_hash="hashed:secret",
            purpose=VerificationTokenPurpose.EMAIL_VERIFICATION,
            expires_at=_NOW + timedelta(hours=24),
            now=_NOW,
        )
        assert token.used_at is None

    def test_created_at_is_now(self) -> None:
        token = VerificationToken.issue(
            id=uuid4(),
            identity_id=uuid4(),
            token_hash="hashed:secret",
            purpose=VerificationTokenPurpose.EMAIL_VERIFICATION,
            expires_at=_NOW + timedelta(hours=24),
            now=_NOW,
        )
        assert token.created_at == _NOW

    def test_updated_at_is_none(self) -> None:
        token = VerificationToken.issue(
            id=uuid4(),
            identity_id=uuid4(),
            token_hash="hashed:secret",
            purpose=VerificationTokenPurpose.EMAIL_VERIFICATION,
            expires_at=_NOW + timedelta(hours=24),
            now=_NOW,
        )
        assert token.updated_at is None

    def test_raises_when_expires_at_equals_now(self) -> None:
        with pytest.raises(InvalidVerificationTokenExpirationError):
            _ = VerificationToken.issue(
                id=uuid4(),
                identity_id=uuid4(),
                token_hash="hashed:secret",
                purpose=VerificationTokenPurpose.EMAIL_VERIFICATION,
                expires_at=_NOW,
                now=_NOW,
            )

    def test_raises_when_expires_at_is_in_past(self) -> None:
        with pytest.raises(InvalidVerificationTokenExpirationError):
            _ = VerificationToken.issue(
                id=uuid4(),
                identity_id=uuid4(),
                token_hash="hashed:secret",
                purpose=VerificationTokenPurpose.EMAIL_VERIFICATION,
                expires_at=_NOW - timedelta(seconds=1),
                now=_NOW,
            )

    def test_raises_carries_context(self) -> None:
        expires_at = _NOW - timedelta(minutes=5)

        with pytest.raises(InvalidVerificationTokenExpirationError) as exc_info:
            _ = VerificationToken.issue(
                id=uuid4(),
                identity_id=uuid4(),
                token_hash="hashed:secret",
                purpose=VerificationTokenPurpose.EMAIL_VERIFICATION,
                expires_at=expires_at,
                now=_NOW,
            )

        assert exc_info.value.expires_at == expires_at
        assert exc_info.value.now == _NOW


class TestVerificationTokenIsUsed:
    """Метод ``VerificationToken.is_used``."""

    def test_false_for_fresh_token(self) -> None:
        assert _make_token().is_used() is False

    def test_true_after_mark_used(self) -> None:
        token = _make_token()
        token.mark_used(at=_NOW)
        assert token.is_used() is True

    def test_true_after_invalidate(self) -> None:
        token = _make_token()
        token.invalidate(at=_NOW)
        assert token.is_used() is True

    def test_true_for_token_loaded_with_used_at(self) -> None:
        token = _make_token(used_at=_NOW)
        assert token.is_used() is True


class TestVerificationTokenIsExpired:
    """Метод ``VerificationToken.is_expired``."""

    def test_false_before_expiration(self) -> None:
        token = _make_token(expires_in=timedelta(hours=24))
        assert token.is_expired(_NOW) is False

    def test_true_at_expiration_boundary(self) -> None:
        token = _make_token(expires_in=timedelta(hours=24))
        assert token.is_expired(_NOW + timedelta(hours=24)) is True

    def test_true_after_expiration(self) -> None:
        token = _make_token(expires_in=timedelta(hours=24))
        assert token.is_expired(_NOW + timedelta(hours=25)) is True

    def test_uses_current_time_by_default(self) -> None:
        token = _make_token(expires_in=_FAR_FUTURE_LIFETIME)
        assert token.is_expired() is False


class TestVerificationTokenIsUsable:
    """Метод ``VerificationToken.is_usable``."""

    def test_true_for_fresh_token(self) -> None:
        assert _make_token().is_usable(_NOW) is True

    def test_false_for_used_token(self) -> None:
        token = _make_token()
        token.mark_used(at=_NOW)
        assert token.is_usable(_NOW) is False

    def test_false_for_expired_token(self) -> None:
        token = _make_token(expires_in=timedelta(hours=24))
        assert token.is_usable(_NOW + timedelta(hours=25)) is False

    def test_false_for_used_expired_token(self) -> None:
        token = _make_token(expires_in=timedelta(hours=24))
        token.invalidate(at=_NOW)
        assert token.is_usable(_NOW + timedelta(hours=25)) is False


class TestVerificationTokenMarkUsed:
    """Метод ``VerificationToken.mark_used``."""

    def test_sets_used_at(self) -> None:
        token = _make_token()
        token.mark_used(at=_NOW)
        assert token.used_at == _NOW

    def test_sets_updated_at(self) -> None:
        token = _make_token()
        assert token.updated_at is None
        token.mark_used(at=_NOW)
        assert token.updated_at == _NOW

    def test_uses_current_time_by_default(self) -> None:
        token = _make_token(expires_in=_FAR_FUTURE_LIFETIME)
        token.mark_used()
        assert token.used_at is not None
        assert token.updated_at is not None

    def test_does_not_change_created_at(self) -> None:
        token = _make_token()
        token.mark_used(at=_NOW + timedelta(hours=1))
        assert token.created_at == _NOW

    def test_raises_when_expired(self) -> None:
        token = _make_token(expires_in=timedelta(hours=1))

        with pytest.raises(VerificationTokenExpiredError):
            token.mark_used(at=_NOW + timedelta(hours=2))

    def test_raises_when_expired_leaves_token_usable_state_unchanged(self) -> None:
        token = _make_token(expires_in=timedelta(hours=1))

        with pytest.raises(VerificationTokenExpiredError):
            token.mark_used(at=_NOW + timedelta(hours=2))

        assert token.used_at is None
        assert token.updated_at is None

    def test_raises_when_already_applied(self) -> None:
        token = _make_token()
        token.mark_used(at=_NOW)

        with pytest.raises(VerificationTokenAlreadyUsedError):
            token.mark_used(at=_NOW + timedelta(hours=1))

        assert token.used_at == _NOW

    def test_raises_when_already_invalidated(self) -> None:
        token = _make_token()
        token.invalidate(at=_NOW)

        with pytest.raises(VerificationTokenAlreadyUsedError):
            token.mark_used(at=_NOW + timedelta(hours=1))

        assert token.used_at == _NOW

    def test_already_used_takes_precedence_over_expired(self) -> None:
        token = _make_token(expires_in=timedelta(hours=1))
        token.mark_used(at=_NOW)

        with pytest.raises(VerificationTokenAlreadyUsedError):
            token.mark_used(at=_NOW + timedelta(hours=2))

    def test_raises_carries_token_id(self) -> None:
        token = _make_token(expires_in=timedelta(hours=1))

        with pytest.raises(VerificationTokenExpiredError) as exc_info:
            token.mark_used(at=_NOW + timedelta(hours=2))

        assert exc_info.value.token_id == token.id


class TestVerificationTokenInvalidate:
    """Метод ``VerificationToken.invalidate``."""

    def test_sets_used_at(self) -> None:
        token = _make_token()
        token.invalidate(at=_NOW)
        assert token.used_at == _NOW

    def test_sets_updated_at(self) -> None:
        token = _make_token()
        assert token.updated_at is None
        token.invalidate(at=_NOW)
        assert token.updated_at == _NOW

    def test_uses_current_time_by_default(self) -> None:
        token = _make_token()
        token.invalidate()
        assert token.used_at is not None

    def test_idempotent(self) -> None:
        token = _make_token()
        token.invalidate(at=_NOW)
        token.invalidate(at=_NOW + timedelta(hours=1))
        assert token.used_at == _NOW

    def test_allowed_on_expired_token(self) -> None:
        token = _make_token(expires_in=timedelta(hours=1))
        token.invalidate(at=_NOW + timedelta(hours=2))
        assert token.used_at == _NOW + timedelta(hours=2)

    def test_equivalent_to_mark_used(self) -> None:
        invalidated = _make_token()
        applied = _make_token()
        invalidated.invalidate(at=_NOW)
        applied.mark_used(at=_NOW)
        assert invalidated.used_at == applied.used_at

    def test_prevents_later_mark_used(self) -> None:
        token = _make_token()
        token.invalidate(at=_NOW)

        with pytest.raises(VerificationTokenAlreadyUsedError):
            token.mark_used(at=_NOW + timedelta(hours=1))

        assert token.used_at == _NOW


class TestVerificationTokenRepr:
    """Строковое представление ``VerificationToken``."""

    def test_contains_purpose(self) -> None:
        assert "EMAIL_VERIFICATION" in repr(_make_token())

    def test_contains_used_at(self) -> None:
        token = _make_token()
        token.mark_used(at=_NOW)
        assert "used_at=" in repr(token)

    def test_does_not_leak_token_hash(self) -> None:
        assert "hashed:secret" not in repr(_make_token())
