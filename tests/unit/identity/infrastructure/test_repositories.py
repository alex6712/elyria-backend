"""Unit-тесты SQLAlchemy-репозиториев на фейковом соединении."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import Insert, Select, Update
from sqlalchemy.exc import IntegrityError

from src.identity.domain.entities import Identity, Profile, Session
from src.identity.domain.exceptions import UsernameAlreadyExistsError
from src.identity.domain.value_objects import DisplayName, Username
from src.identity.infrastructure.persistence import (
    SqlAlchemyIdentityRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemySessionRepository,
)
from src.shared.domain.exceptions import ConcurrentModificationError
from tests.fakes.sqlalchemy import FakeConnection, FakeDBAPIError, FakeResult

UUID_ONE = UUID("11111111-1111-1111-1111-111111111111")
UUID_TWO = UUID("22222222-2222-2222-2222-222222222222")
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def make_identity(**overrides) -> Identity:
    """Создать учётную запись с базовыми значениями."""
    defaults = dict(
        id=UUID_ONE,
        username=Username("alice"),
        password_hash="hash",
        is_active=True,
        version=1,
        created_at=NOW,
        updated_at=None,
    )
    defaults.update(overrides)
    return Identity(**defaults)


def make_profile(**overrides) -> Profile:
    """Создать профиль с базовыми значениями."""
    defaults = dict(
        id=UUID_TWO,
        identity_id=UUID_ONE,
        display_name=DisplayName("Alice"),
        avatar_url=None,
        version=1,
        created_at=NOW,
        updated_at=None,
    )
    defaults.update(overrides)
    return Profile(**defaults)


def make_session(**overrides) -> Session:
    """Создать сессию с базовыми значениями."""
    defaults = dict(
        id=UUID_TWO,
        identity_id=UUID_ONE,
        session_secret="secret",
        expires_at=NOW + timedelta(days=30),
        last_used_at=NOW,
        revoked_at=None,
        ip_address=None,
        user_agent=None,
        version=1,
        created_at=NOW,
        updated_at=None,
    )
    defaults.update(overrides)
    return Session(**defaults)


class TestSqlAlchemyIdentityRepository:
    """Проверка репозитория учётных записей."""

    async def test_add_executes_insert_with_entity_values(self) -> None:
        """add() выполняет INSERT со всеми полями сущности."""
        connection = FakeConnection()
        repository = SqlAlchemyIdentityRepository(connection)

        await repository.add(make_identity())

        stmt = connection.executed[0]
        assert isinstance(stmt, Insert)
        params = stmt.compile().params
        assert params["id"] == UUID_ONE
        assert params["username"] == Username("alice")
        assert params["password_hash"] == "hash"
        assert params["is_active"] is True
        assert params["version"] == 1

    async def test_add_username_conflict_raises_domain_error(self) -> None:
        """Конфликт имени пользователя транслируется в доменную ошибку."""
        connection = FakeConnection()
        connection.error = IntegrityError(
            "INSERT INTO identities",
            {},
            FakeDBAPIError(
                'duplicate key value violates unique constraint "uq_users_username"'
            ),
        )
        repository = SqlAlchemyIdentityRepository(connection)

        with pytest.raises(UsernameAlreadyExistsError):
            await repository.add(make_identity())

    async def test_add_unrelated_integrity_error_reraises(self) -> None:
        """Посторонний IntegrityError пробрасывается без изменений."""
        connection = FakeConnection()
        connection.error = IntegrityError(
            "INSERT INTO identities", {}, FakeDBAPIError("some other failure")
        )
        repository = SqlAlchemyIdentityRepository(connection)

        with pytest.raises(IntegrityError):
            await repository.add(make_identity())

    async def test_get_by_id_maps_row_to_identity(self) -> None:
        """get_by_id() восстанавливает сущность из строки результата."""
        connection = FakeConnection()
        connection.result = FakeResult(
            row={
                "id": UUID_ONE,
                "username": "alice",
                "password_hash": "hash",
                "is_active": True,
                "version": 3,
                "created_at": NOW,
                "updated_at": None,
            }
        )
        repository = SqlAlchemyIdentityRepository(connection)

        identity = await repository.get_by_id(UUID_ONE)

        assert identity is not None
        assert identity.id == UUID_ONE
        # TODO: репозиторий не оборачивает username в value object Username,
        # возвращая голую строку; зафиксировано текущее поведение.
        assert identity.username == "alice"
        assert identity.version == 3
        assert isinstance(connection.executed[0], Select)

    async def test_get_by_id_missing_returns_none(self) -> None:
        """get_by_id() возвращает None, если запись не найдена."""
        connection = FakeConnection()
        connection.result = FakeResult(row=None)
        repository = SqlAlchemyIdentityRepository(connection)

        assert await repository.get_by_id(UUID_ONE) is None

    async def test_get_by_username_filters_by_username(self) -> None:
        """get_by_username() выполняет выборку по имени пользователя."""
        connection = FakeConnection()
        connection.result = FakeResult(
            row={
                "id": UUID_ONE,
                "username": "alice",
                "password_hash": "hash",
                "is_active": True,
                "version": 1,
                "created_at": NOW,
                "updated_at": None,
            }
        )
        repository = SqlAlchemyIdentityRepository(connection)

        identity = await repository.get_by_username(Username("alice"))

        assert identity is not None
        assert str(identity.username) == "alice"

    async def test_get_by_username_missing_returns_none(self) -> None:
        """get_by_username() возвращает None, если запись не найдена."""
        connection = FakeConnection()
        connection.result = FakeResult(row=None)
        repository = SqlAlchemyIdentityRepository(connection)

        assert await repository.get_by_username(Username("alice")) is None

    async def test_save_password_hash_success_upgrades_version(self) -> None:
        """Успешное обновление увеличивает версию сущности."""
        connection = FakeConnection()
        connection.result = FakeResult(rowcount=1)
        repository = SqlAlchemyIdentityRepository(connection)
        identity = make_identity()

        await repository.save_password_hash(identity)

        assert identity.version == 2
        stmt = connection.executed[0]
        assert isinstance(stmt, Update)
        assert stmt.compile().params["password_hash"] == "hash"

    async def test_save_password_hash_conflict_raises(self) -> None:
        """Несовпадение версии вызывает ConcurrentModificationError."""
        connection = FakeConnection()
        connection.result = FakeResult(rowcount=0)
        repository = SqlAlchemyIdentityRepository(connection)

        with pytest.raises(ConcurrentModificationError):
            await repository.save_password_hash(make_identity())


class TestSqlAlchemyProfileRepository:
    """Проверка репозитория профилей."""

    async def test_add_executes_insert(self) -> None:
        """add() выполняет INSERT со значениями профиля."""
        connection = FakeConnection()
        repository = SqlAlchemyProfileRepository(connection)

        await repository.add(make_profile())

        stmt = connection.executed[0]
        assert isinstance(stmt, Insert)
        params = stmt.compile().params
        assert params["identity_id"] == UUID_ONE
        assert params["display_name"] == "Alice"
        assert params["avatar_url"] is None

    async def test_get_by_identity_id_maps_row(self) -> None:
        """get_by_identity_id() восстанавливает профиль из строки."""
        connection = FakeConnection()
        connection.result = FakeResult(
            row={
                "id": UUID_TWO,
                "identity_id": UUID_ONE,
                "display_name": "Alice",
                "avatar_url": "https://cdn.example.com/a.png",
                "version": 1,
                "created_at": NOW,
                "updated_at": None,
            }
        )
        repository = SqlAlchemyProfileRepository(connection)

        profile = await repository.get_by_identity_id(UUID_ONE)

        assert profile is not None
        assert profile.display_name == DisplayName("Alice")
        assert profile.avatar_url == "https://cdn.example.com/a.png"

    async def test_get_by_identity_id_missing_returns_none(self) -> None:
        """get_by_identity_id() возвращает None, если профиль не найден."""
        connection = FakeConnection()
        connection.result = FakeResult(row=None)
        repository = SqlAlchemyProfileRepository(connection)

        assert await repository.get_by_identity_id(UUID_ONE) is None

    async def test_save_display_name_success_upgrades_version(self) -> None:
        """Успешное обновление имени увеличивает версию профиля."""
        connection = FakeConnection()
        connection.result = FakeResult(rowcount=1)
        repository = SqlAlchemyProfileRepository(connection)
        profile = make_profile(display_name=DisplayName("Alicia"))

        await repository.save_display_name(profile)

        assert profile.version == 2
        assert connection.executed[0].compile().params["display_name"] == "Alicia"

    async def test_save_display_name_conflict_raises(self) -> None:
        """Несовпадение версии вызывает ConcurrentModificationError."""
        connection = FakeConnection()
        connection.result = FakeResult(rowcount=0)
        repository = SqlAlchemyProfileRepository(connection)

        with pytest.raises(ConcurrentModificationError):
            await repository.save_display_name(make_profile())


class TestSqlAlchemySessionRepository:
    """Проверка репозитория сессий."""

    async def test_add_executes_insert(self) -> None:
        """add() выполняет INSERT со всеми полями сессии."""
        connection = FakeConnection()
        repository = SqlAlchemySessionRepository(connection)

        await repository.add(
            make_session(ip_address="192.168.1.1", user_agent="curl/8.0")
        )

        stmt = connection.executed[0]
        assert isinstance(stmt, Insert)
        params = stmt.compile().params
        assert params["session_secret"] == "secret"
        assert params["ip_address"] == "192.168.1.1"
        assert params["user_agent"] == "curl/8.0"

    async def test_get_by_id_maps_row(self) -> None:
        """get_by_id() восстанавливает сессию из строки."""
        connection = FakeConnection()
        connection.result = FakeResult(
            row={
                "id": UUID_TWO,
                "identity_id": UUID_ONE,
                "session_secret": "secret",
                "expires_at": NOW + timedelta(days=30),
                "last_used_at": NOW,
                "revoked_at": NOW,
                "ip_address": None,
                "user_agent": None,
                "version": 4,
                "created_at": NOW,
                "updated_at": NOW,
            }
        )
        repository = SqlAlchemySessionRepository(connection)

        session = await repository.get_by_id(UUID_TWO)

        assert session is not None
        assert session.session_secret == "secret"
        assert session.revoked_at == NOW
        assert session.version == 4

    async def test_get_by_id_missing_returns_none(self) -> None:
        """get_by_id() возвращает None, если сессия не найдена."""
        connection = FakeConnection()
        connection.result = FakeResult(row=None)
        repository = SqlAlchemySessionRepository(connection)

        assert await repository.get_by_id(UUID_TWO) is None

    async def test_get_by_session_secret_maps_row(self) -> None:
        """get_by_session_secret() восстанавливает сессию из строки."""
        connection = FakeConnection()
        connection.result = FakeResult(
            row={
                "id": UUID_TWO,
                "identity_id": UUID_ONE,
                "session_secret": "secret",
                "expires_at": NOW + timedelta(days=30),
                "last_used_at": NOW,
                "revoked_at": None,
                "ip_address": None,
                "user_agent": None,
                "version": 1,
                "created_at": NOW,
                "updated_at": None,
            }
        )
        repository = SqlAlchemySessionRepository(connection)

        session = await repository.get_by_session_secret("secret")

        assert session is not None
        assert session.session_secret == "secret"
        assert isinstance(connection.executed[0], Select)

    async def test_get_by_session_secret_missing_returns_none(self) -> None:
        """get_by_session_secret() возвращает None, если сессия не найдена."""
        connection = FakeConnection()
        connection.result = FakeResult(row=None)
        repository = SqlAlchemySessionRepository(connection)

        assert await repository.get_by_session_secret("secret") is None

    async def test_mark_used_returns_true_on_update(self) -> None:
        """mark_used() возвращает True при успешном обновлении."""
        connection = FakeConnection()
        connection.result = FakeResult(rowcount=1)
        repository = SqlAlchemySessionRepository(connection)

        assert await repository.mark_used(UUID_TWO, NOW) is True

    async def test_mark_used_returns_false_on_missing(self) -> None:
        """mark_used() возвращает False, если сессия не найдена."""
        connection = FakeConnection()
        connection.result = FakeResult(rowcount=0)
        repository = SqlAlchemySessionRepository(connection)

        assert await repository.mark_used(UUID_TWO, NOW) is False

    async def test_save_rotation_success_upgrades_version(self) -> None:
        """Успешная ротация увеличивает версию сессии."""
        connection = FakeConnection()
        connection.result = FakeResult(rowcount=1)
        repository = SqlAlchemySessionRepository(connection)
        session = make_session(session_secret="new-secret")

        await repository.save_rotation(session)

        assert session.version == 2
        params = connection.executed[0].compile().params
        assert params["session_secret"] == "new-secret"

    async def test_save_rotation_conflict_raises(self) -> None:
        """Несовпадение версии вызывает ConcurrentModificationError."""
        connection = FakeConnection()
        connection.result = FakeResult(rowcount=0)
        repository = SqlAlchemySessionRepository(connection)

        with pytest.raises(ConcurrentModificationError):
            await repository.save_rotation(make_session())

    async def test_save_revocation_success_upgrades_version(self) -> None:
        """Успешный отзыв увеличивает версию сессии."""
        connection = FakeConnection()
        connection.result = FakeResult(rowcount=1)
        repository = SqlAlchemySessionRepository(connection)
        session = make_session(revoked_at=NOW)

        await repository.save_revocation(session)

        assert session.version == 2
        assert connection.executed[0].compile().params["revoked_at"] == NOW

    async def test_save_revocation_conflict_raises(self) -> None:
        """Несовпадение версии вызывает ConcurrentModificationError."""
        connection = FakeConnection()
        connection.result = FakeResult(rowcount=0)
        repository = SqlAlchemySessionRepository(connection)

        with pytest.raises(ConcurrentModificationError):
            await repository.save_revocation(make_session())

    async def test_revoke_all_by_identity_id_returns_count(self) -> None:
        """revoke_all_by_identity_id() возвращает число обновлённых строк."""
        connection = FakeConnection()
        connection.result = FakeResult(rowcount=3)
        repository = SqlAlchemySessionRepository(connection)

        count = await repository.revoke_all_by_identity_id(UUID_ONE)

        assert count == 3
        stmt = connection.executed[0]
        assert isinstance(stmt, Update)
        assert stmt.compile().params["revoked_at"] is not None
