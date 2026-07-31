"""Unit-тесты общих доменных примесей и исключений.

Покрывают :class:`Identifiable`, :class:`Auditable`,
:class:`Versioned` из ``src/shared/domain/entities`` и
:class:`ConcurrentModificationError`.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.identity.domain.entities import Identity, Profile, Session
from src.identity.domain.value_objects import DisplayName, Username
from src.shared.domain.entities import Auditable, Identifiable, Versioned
from src.shared.domain.exceptions import ConcurrentModificationError


class _SimpleEntity(Identifiable[str], Auditable, Versioned):
    """Вспомогательная сущность для проверки примесей."""

    def __init__(self, id: str, created_at: datetime) -> None:
        Identifiable.__init__(self, id)
        Auditable.__init__(self, created_at, None)
        Versioned.__init__(self, 1)


class TestIdentifiable:
    """Проверка примеси идентичности."""

    def test_equality_by_id_and_class(self) -> None:
        """Сущности одного класса с одинаковым id равны."""
        entity_id = uuid4()
        first = _SimpleEntity(entity_id, datetime.now(UTC))
        second = _SimpleEntity(entity_id, datetime.now(UTC))

        assert first == second

    def test_inequality_for_different_ids(self) -> None:
        """Сущности одного класса с разными id не равны."""
        first = _SimpleEntity(uuid4(), datetime.now(UTC))
        second = _SimpleEntity(uuid4(), datetime.now(UTC))

        assert first != second

    def test_inequality_for_different_classes(self) -> None:
        """Сущности разных классов с одинаковым id не равны."""
        entity_id = uuid4()
        identity = Identity(
            id=entity_id,
            username=Username("john_doe"),
            password_hash="hash",
            is_active=True,
            version=1,
            created_at=datetime.now(UTC),
            updated_at=None,
        )
        profile = Profile(
            id=entity_id,
            identity_id=uuid4(),
            display_name=DisplayName("John"),
            avatar_url=None,
            version=1,
            created_at=datetime.now(UTC),
            updated_at=None,
        )

        assert identity != profile

    def test_inequality_for_unrelated_object(self) -> None:
        """Сравнение с посторонним объектом даёт False."""
        entity = _SimpleEntity(uuid4(), datetime.now(UTC))

        assert entity != "not an entity"

    def test_hash_consistent_with_equality(self) -> None:
        """Хеш согласован с равенством: равен только при равных id."""
        entity_id = uuid4()
        first = _SimpleEntity(entity_id, datetime.now(UTC))
        second = _SimpleEntity(entity_id, datetime.now(UTC))

        assert hash(first) == hash(second)


class TestAuditable:
    """Проверка примеси временных меток аудита."""

    def test_touch_with_explicit_at(self) -> None:
        """Явная метка времени фиксируется как updated_at."""
        created_at = datetime.now(UTC)
        moment = created_at - timedelta(days=1)
        entity = _SimpleEntity(uuid4(), created_at)

        entity._touch(moment)

        assert entity.updated_at == moment

    def test_touch_without_at_sets_now(self) -> None:
        """Без метки времени updated_at получает текущий момент."""
        before = datetime.now(UTC)
        entity = _SimpleEntity(uuid4(), before)

        entity._touch()

        assert entity.updated_at is not None
        assert entity.updated_at >= before


class TestVersioned:
    """Проверка примеси версии агрегата."""

    def test_upgrade_increments_version(self) -> None:
        """Метод upgrade увеличивает версию ровно на 1."""
        entity = _SimpleEntity(uuid4(), datetime.now(UTC))
        initial_version = entity.version

        entity.upgrade()

        assert entity.version == initial_version + 1

    def test_version_starts_at_one_via_factories(self) -> None:
        """Сущности, созданные фабриками, начинаются с версии 1."""
        session = Session.issue(
            id=uuid4(),
            identity_id=uuid4(),
            session_secret="secret",
            expires_at=datetime(2026, 12, 31, tzinfo=UTC),
        )

        assert session.version == 1


class TestConcurrentModificationError:
    """Проверка исключения оптимистичной блокировки."""

    def test_message_and_attributes(self) -> None:
        """Исключение содержит идентификатор и тип сущности."""
        entity_id = uuid4()

        error = ConcurrentModificationError(entity_id, "Identity")

        assert error.entity_id == entity_id
        assert error.entity_type == "Identity"
        assert str(entity_id) in str(error)
        assert "Identity" in str(error)
