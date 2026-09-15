"""Unit-тесты ``Identity`` (domain entity) с ``email``."""

import pytest

from src.users.domain.entities import Identity
from src.users.domain.exceptions import InactiveUserError
from src.users.domain.value_objects import Email, Username


def _make_identity(
    *,
    username: str = "john_doe",
    email: str = "john@example.com",
) -> Identity:
    """Создать ``Identity`` с указанными параметрами."""
    return Identity.register(
        username=Username(username),
        password_hash="hash:secret",
        email=Email(email),
    )


class TestIdentityRegister:
    """Фабрика ``Identity.register``."""

    def test_sets_email(self) -> None:
        identity = _make_identity(email="alice@test.com")
        assert identity.email.value == "alice@test.com"

    def test_email_verified_is_false(self) -> None:
        identity = _make_identity()
        assert identity.email_verified is False

    def test_is_active(self) -> None:
        identity = _make_identity()
        assert identity.is_active is True

    def test_version_is_one(self) -> None:
        identity = _make_identity()
        assert identity.version == 1

    def test_created_at_is_set(self) -> None:
        identity = _make_identity()
        assert identity.created_at is not None

    def test_updated_at_is_none(self) -> None:
        identity = _make_identity()
        assert identity.updated_at is None


class TestIdentityVerifyEmail:
    """Метод ``Identity.verify_email``."""

    def test_sets_email_verified_true(self) -> None:
        identity = _make_identity()
        identity.verify_email()
        assert identity.email_verified is True

    def test_version_unchanged_in_memory(self) -> None:
        identity = _make_identity()
        v_before = identity.version
        identity.verify_email()
        assert identity.version == v_before

    def test_sets_updated_at(self) -> None:
        identity = _make_identity()
        assert identity.updated_at is None
        identity.verify_email()
        assert identity.updated_at is not None

    def test_idempotent(self) -> None:
        identity = _make_identity()
        identity.verify_email()
        v_after_first = identity.version
        identity.verify_email()
        assert identity.version == v_after_first

    def test_raises_on_inactive_user(self) -> None:
        identity = _make_identity()
        identity.deactivate()
        with pytest.raises(InactiveUserError):
            identity.verify_email()

    def test_allows_activate_then_verify(self) -> None:
        identity = _make_identity()
        identity.deactivate()
        identity.activate()
        identity.verify_email()
        assert identity.email_verified is True


class TestIdentityRepr:
    """Строковое представление ``Identity``."""

    def test_contains_email(self) -> None:
        identity = _make_identity(email="jane@test.com")
        assert "email=" in repr(identity)
        assert "jane@test.com" in repr(identity)

    def test_contains_email_verified(self) -> None:
        identity = _make_identity()
        assert "email_verified=False" in repr(identity)
