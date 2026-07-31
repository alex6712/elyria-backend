"""Unit-тесты доменной сущности :class:`Identity`."""

from datetime import UTC, datetime

import pytest

from src.identity.domain.entities import Identity
from src.identity.domain.exceptions import InactiveUserError
from src.identity.domain.value_objects import Username

USERNAME = "john_doe"
PASSWORD_HASH = "hash:old_password"


@pytest.fixture
def identity() -> Identity:
    """Учётная запись, созданная через фабричный метод."""
    return Identity.register(Username(USERNAME), PASSWORD_HASH)


class TestIdentityRegister:
    """Проверка фабричного метода регистрации."""

    def test_register_creates_active_identity(self, identity: Identity) -> None:
        """Новая учётная запись активна."""
        assert identity.is_active is True

    def test_register_sets_defaults(self, identity: Identity) -> None:
        """Новая учётная запись имеет начальные значения версии и аудита."""
        assert identity.version == 1
        assert identity.updated_at is None
        assert identity.created_at is not None

    def test_register_preserves_password_hash(self) -> None:
        """Хэш пароля сохраняется без изменений."""
        identity = Identity.register(Username(USERNAME), PASSWORD_HASH)

        assert identity.password_hash == PASSWORD_HASH

    def test_register_generates_unique_ids(self) -> None:
        """Каждая новая учётная запись получает уникальный идентификатор."""
        first = Identity.register(Username(USERNAME), PASSWORD_HASH)
        second = Identity.register(Username("other_user"), PASSWORD_HASH)

        assert first.id != second.id


class TestIdentityChangePasswordHash:
    """Проверка смены хэша пароля."""

    def test_changes_hash_for_active_user(self, identity: Identity) -> None:
        """Активному пользователю хэш пароля меняется."""
        identity.change_password_hash("hash:new_password")

        assert identity.password_hash == "hash:new_password"
        assert identity.updated_at is not None

    def test_raises_for_inactive_user(self, identity: Identity) -> None:
        """Неактивному пользователю хэш пароля менять запрещено."""
        identity.deactivate()

        with pytest.raises(InactiveUserError) as exc_info:
            identity.change_password_hash("hash:new_password")

        assert exc_info.value.user_id == identity.id
        assert identity.password_hash == PASSWORD_HASH

    def test_explicit_at_is_used(self, identity: Identity) -> None:
        """Переданная метка времени фиксируется как updated_at."""
        moment = datetime(2026, 1, 1, tzinfo=UTC)

        identity.change_password_hash("hash:new_password", at=moment)

        assert identity.updated_at == moment


class TestIdentityDeactivate:
    """Проверка деактивации учётной записи."""

    def test_deactivate_active_user(self, identity: Identity) -> None:
        """Активная учётная запись деактивируется и обновляет updated_at."""
        identity.deactivate()

        assert identity.is_active is False
        assert identity.updated_at is not None

    def test_deactivate_is_idempotent(self, identity: Identity) -> None:
        """Повторная деактивация не изменяет состояние и updated_at."""
        identity.deactivate()
        updated_at = identity.updated_at

        identity.deactivate()

        assert identity.is_active is False
        assert identity.updated_at == updated_at

    def test_deactivate_with_explicit_at(self, identity: Identity) -> None:
        """Переданная метка времени фиксируется как updated_at."""
        moment = datetime(2026, 1, 1, tzinfo=UTC)

        identity.deactivate(at=moment)

        assert identity.updated_at == moment


class TestIdentityActivate:
    """Проверка активации учётной записи."""

    def test_activate_inactive_user(self, identity: Identity) -> None:
        """Неактивная учётная запись активируется."""
        identity.deactivate()

        identity.activate()

        assert identity.is_active is True
        assert identity.updated_at is not None

    def test_activate_is_idempotent(self, identity: Identity) -> None:
        """Повторная активация не изменяет состояние и updated_at."""
        identity.deactivate()
        identity.activate()
        updated_at = identity.updated_at

        identity.activate()

        assert identity.is_active is True
        assert identity.updated_at == updated_at

    def test_activate_allowed_for_inactive_user(self, identity: Identity) -> None:
        """Активация — единственная операция, разрешённая неактивному пользователю."""
        identity.deactivate()

        identity.activate()

        assert identity.is_active is True


class TestIdentityRepresentation:
    """Проверка строкового представления."""

    def test_repr_contains_key_fields(self, identity: Identity) -> None:
        """Представление содержит ключевые поля учётной записи."""
        assert "Identity(" in repr(identity)
        assert str(identity.id) in repr(identity)
        assert "john_doe" in repr(identity)
