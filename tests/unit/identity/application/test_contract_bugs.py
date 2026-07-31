"""Контрактные xfail-тесты: фиксация известных багов.

Тесты описывают ожидаемое (контрактное) поведение компонентов,
которое в настоящее время нарушено. Пока баги не исправлены,
тесты падают и помечены ``xfail``; после исправления они
станут ``XPASS``, что сигнализирует о закрытии тикета.

Каждый тест содержит ``TODO`` с описанием проблемы.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError

from src.identity.application.commands import (
    LoginCommand,
    RefreshSessionCommand,
)
from src.identity.application.dto import TokenClaimsDTO
from src.identity.application.exceptions import SessionNotFoundError
from src.identity.application.use_cases import (
    LoginUseCase,
    RefreshSessionUseCase,
)
from src.identity.domain.entities import Identity, Session
from src.identity.domain.exceptions import (
    InactiveUserError,
    UsernameAlreadyExistsError,
)
from src.identity.domain.value_objects import Username
from src.identity.infrastructure.persistence import SqlAlchemyIdentityRepository
from tests.fakes.security import (
    FakePasswordHasher,
    FakeTokenHasher,
    FakeTokenIssuer,
)
from tests.fakes.sqlalchemy import FakeConnection, FakeDBAPIError, FakeResult

UUID_ONE = UUID("11111111-1111-1111-1111-111111111111")
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


class TestLoginInactiveUserContract:
    """TODO: LoginUseCase не проверяет признак ``is_active``.

    Доменное исключение ``InactiveUserError`` определено, но нигде
    не выбрасывается. Контракт: вход для неактивной учётной записи
    должен завершаться ошибкой.
    """

    @pytest.mark.xfail(
        reason="TODO: LoginUseCase игнорирует is_active",
        strict=False,
    )
    async def test_login_inactive_user_raises(
        self,
        uow,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Вход неактивного пользователя отклоняется."""
        await uow.identities.add(
            make_identity(
                is_active=False, password_hash=password_hasher.hash("password")
            )
        )
        use_case = LoginUseCase(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        with pytest.raises(InactiveUserError):
            await use_case.execute(LoginCommand(username="alice", password="password"))


class TestRefreshRevokedSessionContract:
    """TODO: refresh отозванной сессии даёт SessionInvalidError.

    Контракт (докстринг RefreshSessionUseCase): отозванная сессия
    должна транслироваться в ``SessionNotFoundError``. Фактически
    ``Session.rotate_secret`` выбрасывает ``SessionInvalidError``,
    который не перехватывается.
    """

    @pytest.fixture
    def refresh_use_case(
        self,
        uow,
        token_issuer: FakeTokenIssuer,
        token_verifier,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> RefreshSessionUseCase:
        """Use case обновления сессии на фейках."""
        return RefreshSessionUseCase(
            uow=uow,
            token_issuer=token_issuer,
            token_verifier=token_verifier,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

    @pytest.mark.xfail(
        reason="TODO: rotate_secret не транслируется в SessionNotFoundError",
        strict=False,
    )
    async def test_refresh_revoked_session_raises_not_found(
        self, refresh_use_case, uow, token_verifier, token_hasher
    ) -> None:
        """Обновление токена отозванной сессии даёт SessionNotFoundError."""
        session = Session(
            id=UUID_ONE,
            identity_id=UUID_ONE,
            session_secret=token_hasher.hash("token"),
            expires_at=NOW + timedelta(days=30),
            last_used_at=NOW,
            revoked_at=NOW,
            ip_address=None,
            user_agent=None,
            version=1,
            created_at=NOW,
            updated_at=None,
        )
        await uow.sessions.add(session)
        token_verifier.claims = TokenClaimsDTO(
            user_id=UUID_ONE,
            session_id=UUID_ONE,
            token_id=UUID_ONE,
            expires_at=NOW + timedelta(days=30),
            issued_at=NOW,
        )

        with pytest.raises(SessionNotFoundError):
            await refresh_use_case.execute(RefreshSessionCommand(refresh_token="token"))

    @pytest.mark.xfail(
        reason="TODO: rotate_secret истёкшей сессии не транслируется",
        strict=False,
    )
    async def test_refresh_expired_session_raises_not_found(
        self, refresh_use_case, uow, token_verifier, token_hasher
    ) -> None:
        """Обновление токена истёкшей сессии даёт SessionNotFoundError."""
        session = Session(
            id=UUID_ONE,
            identity_id=UUID_ONE,
            session_secret=token_hasher.hash("token"),
            expires_at=NOW - timedelta(days=1),
            last_used_at=NOW,
            revoked_at=None,
            ip_address=None,
            user_agent=None,
            version=1,
            created_at=NOW,
            updated_at=None,
        )
        await uow.sessions.add(session)
        token_verifier.claims = TokenClaimsDTO(
            user_id=UUID_ONE,
            session_id=UUID_ONE,
            token_id=UUID_ONE,
            expires_at=NOW + timedelta(days=30),
            issued_at=NOW,
        )

        with pytest.raises(SessionNotFoundError):
            await refresh_use_case.execute(RefreshSessionCommand(refresh_token="token"))


class TestUsernameConstraintNameContract:
    """TODO: репозиторий ищет констрейнт ``uq_users_username``.

    Реальный констрейнт таблицы ``identities`` называется
    ``uq_identities_username``. При дубликате имени репозиторий
    не распознаёт ошибку и пробрасывает ``IntegrityError`` вместо
    доменного ``UsernameAlreadyExistsError``.
    """

    @pytest.mark.xfail(
        reason="TODO: имя констрейнта uq_users_username",
        strict=False,
    )
    async def test_duplicate_username_translates_to_domain_error(self) -> None:
        """Конфликт по реальному имени констрейнта даёт доменную ошибку."""
        connection = FakeConnection()
        connection.error = IntegrityError(
            "INSERT INTO identities",
            {},
            FakeDBAPIError(
                "duplicate key value violates unique constraint "
                '"uq_identities_username"'
            ),
        )
        repository = SqlAlchemyIdentityRepository(connection)

        with pytest.raises(UsernameAlreadyExistsError):
            await repository.add(make_identity())


class TestRepositoryUsernameValueObjectContract:
    """TODO: репозиторий возвращает голую строку вместо ``Username``.

    ``SqlAlchemyIdentityRepository.get_by_id`` не оборачивает
    ``username`` из строки результата в value object ``Username``,
    нарушая типизацию доменной сущности.
    """

    @pytest.mark.xfail(
        reason="TODO: get_by_id/get_by_username не оборачивают username в Username",
        strict=False,
    )
    async def test_get_by_id_returns_username_value_object(self) -> None:
        """Восстановленная сущность содержит Username, а не строку."""
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

        identity = await repository.get_by_id(UUID_ONE)

        assert identity is not None
        assert isinstance(identity.username, Username)


class TestRevokeAllTimeZoneContract:
    """TODO: ``revoke_all_by_identity_id`` использует naive datetime.

    Колонка ``revoked_at`` объявлена как ``DateTime(timezone=True)``,
    а в ``UPDATE`` передаётся ``datetime.now()`` без часового пояса.
    """

    @pytest.mark.xfail(
        reason="TODO: naive datetime.now() в revoke_all_by_identity_id",
        strict=False,
    )
    def test_revoke_all_uses_aware_datetime(self) -> None:
        """Значение revoked_at содержит часовой пояс."""
        from src.identity.infrastructure.persistence import (
            SqlAlchemySessionRepository,
        )

        connection = FakeConnection()
        connection.result = FakeResult(rowcount=1)
        repository = SqlAlchemySessionRepository(connection)

        import asyncio

        asyncio.run(repository.revoke_all_by_identity_id(UUID_ONE))

        revoked_at = connection.executed[0].compile().params["revoked_at"]
        assert revoked_at.tzinfo is not None
