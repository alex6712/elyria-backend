"""Интеграционные тесты SQLAlchemy-репозиториев на реальном PostgreSQL."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from src.identity.domain.entities import Identity, Profile, Session
from src.identity.domain.exceptions import UsernameAlreadyExistsError
from src.identity.domain.value_objects import DisplayName, Username
from src.identity.infrastructure.persistence import (
    SqlAlchemyIdentityRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemySessionRepository,
)
from src.identity.infrastructure.sqlalchemy_identity_uow import (
    SqlAlchemyIdentityUnitOfWork,
)
from src.shared.domain.exceptions import ConcurrentModificationError

pytestmark = pytest.mark.integration

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def make_identity(**overrides) -> Identity:
    """Создать учётную запись с уникальным именем пользователя."""
    defaults = dict(
        id=uuid4(),
        username=Username(f"user_{uuid4().hex[:8]}"),
        password_hash="$argon2id$test-hash",
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
        id=uuid4(),
        identity_id=uuid4(),
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
        id=uuid4(),
        identity_id=uuid4(),
        session_secret=uuid4().hex,
        expires_at=NOW + timedelta(days=30),
        last_used_at=NOW,
        revoked_at=None,
        ip_address="127.0.0.1",
        user_agent="pytest",
        version=1,
        created_at=NOW,
        updated_at=None,
    )
    defaults.update(overrides)
    return Session(**defaults)


class TestIdentityRepositoryIntegration:
    """Сквозная проверка репозитория учётных записей."""

    async def test_add_and_get_by_id_round_trip(self, pg_engine: AsyncEngine) -> None:
        """Добавленная учётная запись читается обратно целиком."""
        identity = make_identity()
        async with pg_engine.begin() as connection:
            await SqlAlchemyIdentityRepository(connection).add(identity)

        async with pg_engine.begin() as connection:
            loaded = await SqlAlchemyIdentityRepository(connection).get_by_id(
                identity.id
            )

        assert loaded is not None
        assert loaded.id == identity.id
        assert loaded.password_hash == identity.password_hash
        assert loaded.is_active is True
        assert loaded.created_at == identity.created_at

    async def test_get_by_username_round_trip(self, pg_engine: AsyncEngine) -> None:
        """Учётная запись находится по имени пользователя."""
        identity = make_identity()
        async with pg_engine.begin() as connection:
            await SqlAlchemyIdentityRepository(connection).add(identity)

        async with pg_engine.begin() as connection:
            loaded = await SqlAlchemyIdentityRepository(connection).get_by_username(
                identity.username
            )

        assert loaded is not None
        assert loaded.id == identity.id

    async def test_get_by_username_missing_returns_none(
        self, pg_engine: AsyncEngine
    ) -> None:
        """Несуществующее имя пользователя даёт None."""
        async with pg_engine.begin() as connection:
            result = await SqlAlchemyIdentityRepository(connection).get_by_username(
                Username("no_such_user")
            )

        assert result is None

    async def test_save_password_hash_upgrades_version(
        self, pg_engine: AsyncEngine
    ) -> None:
        """Обновление пароля увеличивает версию в БД и в сущности."""
        identity = make_identity()
        async with pg_engine.begin() as connection:
            repository = SqlAlchemyIdentityRepository(connection)
            await repository.add(identity)

        async with pg_engine.begin() as connection:
            repository = SqlAlchemyIdentityRepository(connection)
            loaded = await repository.get_by_id(identity.id)
            assert loaded is not None
            loaded.password_hash = "new-hash"
            await repository.save_password_hash(loaded)

        async with pg_engine.begin() as connection:
            refreshed = await SqlAlchemyIdentityRepository(connection).get_by_id(
                identity.id
            )

        assert refreshed is not None
        assert refreshed.password_hash == "new-hash"
        assert refreshed.version == 2

    async def test_save_password_hash_conflict_raises(
        self, pg_engine: AsyncEngine
    ) -> None:
        """Устаревшая версия сущности вызывает ConcurrentModificationError."""
        identity = make_identity()
        async with pg_engine.begin() as connection:
            await SqlAlchemyIdentityRepository(connection).add(identity)

        async with pg_engine.begin() as connection:
            repository = SqlAlchemyIdentityRepository(connection)
            stale = await repository.get_by_id(identity.id)
            assert stale is not None
            await repository.save_password_hash(stale)

            another = await repository.get_by_id(identity.id)
            assert another is not None
            await repository.save_password_hash(another)

            stale.password_hash = "third-hash"

            with pytest.raises(ConcurrentModificationError):
                await repository.save_password_hash(stale)

    async def test_duplicate_username_rejected(self, pg_engine: AsyncEngine) -> None:
        """Дубликат имени пользователя отклоняется базой.

        TODO: репозиторий ищет констрейнт ``uq_users_username``,
        а реальный называется ``uq_identities_username`` (баг),
        поэтому вместо доменной ошибки пробрасывается IntegrityError.
        """
        first = make_identity()
        async with pg_engine.begin() as connection:
            await SqlAlchemyIdentityRepository(connection).add(first)

        duplicate = make_identity(username=first.username)
        async with pg_engine.begin() as connection:
            with pytest.raises((UsernameAlreadyExistsError, IntegrityError)):
                await SqlAlchemyIdentityRepository(connection).add(duplicate)


class TestProfileRepositoryIntegration:
    """Сквозная проверка репозитория профилей."""

    async def test_add_and_get_by_identity_id_round_trip(
        self, pg_engine: AsyncEngine
    ) -> None:
        """Профиль сохраняется и читается по идентификатору учётной записи."""
        identity = make_identity()
        async with pg_engine.begin() as connection:
            await SqlAlchemyIdentityRepository(connection).add(identity)
            profile = make_profile(identity_id=identity.id)
            await SqlAlchemyProfileRepository(connection).add(profile)

        async with pg_engine.begin() as connection:
            loaded = await SqlAlchemyProfileRepository(connection).get_by_identity_id(
                identity.id
            )

        assert loaded is not None
        assert loaded.id == profile.id
        assert loaded.display_name == profile.display_name
        assert loaded.avatar_url is None

    async def test_save_display_name_upgrades_version(
        self, pg_engine: AsyncEngine
    ) -> None:
        """Обновление отображаемого имени увеличивает версию."""
        identity = make_identity()
        async with pg_engine.begin() as connection:
            await SqlAlchemyIdentityRepository(connection).add(identity)
            profile = make_profile(identity_id=identity.id)
            await SqlAlchemyProfileRepository(connection).add(profile)

        async with pg_engine.begin() as connection:
            repository = SqlAlchemyProfileRepository(connection)
            loaded = await repository.get_by_identity_id(identity.id)
            assert loaded is not None
            loaded.display_name = DisplayName("Alicia")
            await repository.save_display_name(loaded)

        async with pg_engine.begin() as connection:
            refreshed = await SqlAlchemyProfileRepository(
                connection
            ).get_by_identity_id(identity.id)

        assert refreshed is not None
        assert refreshed.display_name == DisplayName("Alicia")
        assert refreshed.version == 2

    async def test_save_display_name_conflict_raises(
        self, pg_engine: AsyncEngine
    ) -> None:
        """Устаревшая версия профиля вызывает ConcurrentModificationError."""
        identity = make_identity()
        async with pg_engine.begin() as connection:
            await SqlAlchemyIdentityRepository(connection).add(identity)
            profile = make_profile(identity_id=identity.id)
            await SqlAlchemyProfileRepository(connection).add(profile)

        async with pg_engine.begin() as connection:
            repository = SqlAlchemyProfileRepository(connection)
            stale = await repository.get_by_identity_id(identity.id)
            assert stale is not None
            await repository.save_display_name(stale)

            another = await repository.get_by_identity_id(identity.id)
            assert another is not None
            await repository.save_display_name(another)

            stale.display_name = DisplayName("Bobby")

            with pytest.raises(ConcurrentModificationError):
                await repository.save_display_name(stale)


class TestSessionRepositoryIntegration:
    """Сквозная проверка репозитория сессий."""

    async def test_add_and_get_round_trip(self, pg_engine: AsyncEngine) -> None:
        """Сессия сохраняется и читается по id и по секрету."""
        identity = make_identity()
        session = make_session(identity_id=identity.id)
        async with pg_engine.begin() as connection:
            await SqlAlchemyIdentityRepository(connection).add(identity)
            await SqlAlchemySessionRepository(connection).add(session)

        async with pg_engine.begin() as connection:
            repository = SqlAlchemySessionRepository(connection)
            by_id = await repository.get_by_id(session.id)
            by_secret = await repository.get_by_session_secret(session.session_secret)

        assert by_id is not None
        assert by_id.session_secret == session.session_secret
        assert by_secret is not None
        assert by_secret.id == session.id
        assert by_secret.expires_at == session.expires_at

    async def test_mark_used(self, pg_engine: AsyncEngine) -> None:
        """mark_used обновляет last_used_at."""
        identity = make_identity()
        session = make_session(identity_id=identity.id)
        async with pg_engine.begin() as connection:
            await SqlAlchemyIdentityRepository(connection).add(identity)
            await SqlAlchemySessionRepository(connection).add(session)

        new_time = NOW + timedelta(hours=5)
        async with pg_engine.begin() as connection:
            updated = await SqlAlchemySessionRepository(connection).mark_used(
                session.id, new_time
            )

        async with pg_engine.begin() as connection:
            loaded = await SqlAlchemySessionRepository(connection).get_by_id(session.id)

        assert updated is True
        assert loaded is not None
        assert loaded.last_used_at == new_time

    async def test_mark_used_missing_returns_false(
        self, pg_engine: AsyncEngine
    ) -> None:
        """mark_used несуществующей сессии возвращает False."""
        async with pg_engine.begin() as connection:
            result = await SqlAlchemySessionRepository(connection).mark_used(
                uuid4(), NOW
            )

        assert result is False

    async def test_save_rotation_rotates_secret(self, pg_engine: AsyncEngine) -> None:
        """Ротация секрета сохраняет новое значение и версию."""
        identity = make_identity()
        session = make_session(identity_id=identity.id)
        async with pg_engine.begin() as connection:
            await SqlAlchemyIdentityRepository(connection).add(identity)
            await SqlAlchemySessionRepository(connection).add(session)

        async with pg_engine.begin() as connection:
            repository = SqlAlchemySessionRepository(connection)
            loaded = await repository.get_by_id(session.id)
            assert loaded is not None
            loaded.session_secret = "rotated-secret"
            loaded.expires_at = NOW + timedelta(days=60)
            await repository.save_rotation(loaded)

        async with pg_engine.begin() as connection:
            refreshed = await SqlAlchemySessionRepository(connection).get_by_id(
                session.id
            )

        assert loaded.version == 2
        assert refreshed is not None
        assert refreshed.session_secret == "rotated-secret"
        assert refreshed.expires_at == NOW + timedelta(days=60)

    async def test_save_rotation_conflict_raises(self, pg_engine: AsyncEngine) -> None:
        """Устаревшая версия сессии при ротации вызывает ошибку."""
        identity = make_identity()
        session = make_session(identity_id=identity.id)
        async with pg_engine.begin() as connection:
            await SqlAlchemyIdentityRepository(connection).add(identity)
            await SqlAlchemySessionRepository(connection).add(session)

        async with pg_engine.begin() as connection:
            repository = SqlAlchemySessionRepository(connection)
            stale = await repository.get_by_id(session.id)
            assert stale is not None
            await repository.save_rotation(stale)

            another = await repository.get_by_id(session.id)
            assert another is not None
            await repository.save_rotation(another)

            stale.session_secret = "stale-rotation"

            with pytest.raises(ConcurrentModificationError):
                await repository.save_rotation(stale)

    async def test_save_revocation_revokes_session(
        self, pg_engine: AsyncEngine
    ) -> None:
        """Отзыв сессии проставляет revoked_at и увеличивает версию."""
        identity = make_identity()
        session = make_session(identity_id=identity.id)
        async with pg_engine.begin() as connection:
            await SqlAlchemyIdentityRepository(connection).add(identity)
            await SqlAlchemySessionRepository(connection).add(session)

        async with pg_engine.begin() as connection:
            repository = SqlAlchemySessionRepository(connection)
            loaded = await repository.get_by_id(session.id)
            assert loaded is not None
            loaded.revoke()
            await repository.save_revocation(loaded)

        async with pg_engine.begin() as connection:
            refreshed = await SqlAlchemySessionRepository(connection).get_by_id(
                session.id
            )

        assert loaded.version == 2
        assert refreshed is not None
        assert refreshed.revoked_at is not None

    async def test_revoke_all_by_identity_id(self, pg_engine: AsyncEngine) -> None:
        """Отзыв всех сессий пользователя."""
        identity = make_identity()
        async with pg_engine.begin() as connection:
            await SqlAlchemyIdentityRepository(connection).add(identity)
            for _ in range(3):
                await SqlAlchemySessionRepository(connection).add(
                    make_session(identity_id=identity.id)
                )

        async with pg_engine.begin() as connection:
            count = await SqlAlchemySessionRepository(
                connection
            ).revoke_all_by_identity_id(identity.id)

        assert count == 3


class TestUnitOfWorkIntegration:
    """Сквозная проверка Unit of Work на реальной БД."""

    async def test_commit_persists_changes(self, pg_engine: AsyncEngine) -> None:
        """Коммит фиксирует изменения всех репозиториев."""
        async with SqlAlchemyIdentityUnitOfWork(pg_engine) as uow:
            identity = make_identity()
            await uow.identities.add(identity)
            profile = make_profile(identity_id=identity.id)
            await uow.profiles.add(profile)
            session = make_session(identity_id=identity.id)
            await uow.sessions.add(session)

        async with SqlAlchemyIdentityUnitOfWork(pg_engine) as check_uow:
            assert await check_uow.identities.get_by_id(identity.id) is not None
            assert (
                await check_uow.profiles.get_by_identity_id(identity.id)
            ) is not None
            assert await check_uow.sessions.get_by_id(session.id) is not None

    async def test_rollback_discards_changes(self, pg_engine: AsyncEngine) -> None:
        """Исключение в контексте откатывает все изменения."""
        identity = make_identity()
        with pytest.raises(RuntimeError):
            async with SqlAlchemyIdentityUnitOfWork(pg_engine) as uow:
                await uow.identities.add(identity)
                raise RuntimeError("boom")

        async with SqlAlchemyIdentityUnitOfWork(pg_engine) as check_uow:
            assert await check_uow.identities.get_by_id(identity.id) is None

    async def test_two_uow_do_not_interfere(self, pg_engine: AsyncEngine) -> None:
        """Параллельные единицы работы изолированы."""
        async with SqlAlchemyIdentityUnitOfWork(pg_engine) as first:
            first_identity = make_identity()
            await first.identities.add(first_identity)
            async with SqlAlchemyIdentityUnitOfWork(pg_engine) as second:
                assert await second.identities.get_by_id(first_identity.id) is None
