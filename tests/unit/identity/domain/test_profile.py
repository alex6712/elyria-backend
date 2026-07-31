"""Unit-тесты доменной сущности :class:`Profile`."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.identity.domain.entities import Profile
from src.identity.domain.value_objects import DisplayName

IDENTITY_ID = uuid4()
DISPLAY_NAME = "John Doe"
AVATAR_URL = "https://example.com/avatar.png"


@pytest.fixture
def profile() -> Profile:
    """Профиль, созданный через фабричный метод."""
    return Profile.create(IDENTITY_ID, DisplayName(DISPLAY_NAME))


class TestProfileCreate:
    """Проверка фабричного метода создания профиля."""

    def test_create_sets_defaults(self, profile: Profile) -> None:
        """Новый профиль имеет начальные значения версии и аудита."""
        assert profile.version == 1
        assert profile.updated_at is None
        assert profile.created_at is not None
        assert profile.avatar_url is None

    def test_create_binds_identity(self, profile: Profile) -> None:
        """Профиль привязан к переданной учётной записи."""
        assert profile.identity_id == IDENTITY_ID

    def test_create_with_avatar_url(self) -> None:
        """URL аватара сохраняется при передаче."""
        profile = Profile.create(IDENTITY_ID, DisplayName(DISPLAY_NAME), AVATAR_URL)

        assert profile.avatar_url == AVATAR_URL

    def test_create_generates_unique_ids(self) -> None:
        """Каждый профиль получает уникальный идентификатор."""
        first = Profile.create(IDENTITY_ID, DisplayName(DISPLAY_NAME))
        second = Profile.create(IDENTITY_ID, DisplayName(DISPLAY_NAME))

        assert first.id != second.id


class TestProfileChangeDisplayName:
    """Проверка смены отображаемого имени."""

    def test_changes_display_name(self, profile: Profile) -> None:
        """Отображаемое имя меняется и обновляет updated_at."""
        new_name = DisplayName("Jane Doe")

        profile.change_display_name(new_name)

        assert profile.display_name == new_name
        assert profile.updated_at is not None

    def test_explicit_at_is_used(self, profile: Profile) -> None:
        """Переданная метка времени фиксируется как updated_at."""
        moment = datetime(2026, 1, 1, tzinfo=UTC)

        profile.change_display_name(DisplayName("Jane Doe"), at=moment)

        assert profile.updated_at == moment


class TestProfileRepresentation:
    """Проверка строкового представления."""

    def test_repr_contains_key_fields(self, profile: Profile) -> None:
        """Представление содержит ключевые поля профиля."""
        assert "Profile(" in repr(profile)
        assert str(profile.id) in repr(profile)
        assert str(profile.identity_id) in repr(profile)
