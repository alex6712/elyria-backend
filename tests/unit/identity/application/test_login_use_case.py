"""Unit-тесты :class:`LoginUseCase`."""

from datetime import UTC, datetime, timedelta

import pytest

from src.identity.application.commands import LoginCommand
from src.identity.application.exceptions import IncorrectUsernameOrPasswordError
from src.identity.application.use_cases import LoginUseCase
from src.identity.domain.entities import Identity
from src.identity.domain.exceptions import InvalidUsernameLengthError
from src.identity.domain.value_objects import Username
from tests.fakes.identity_uow import FakeIdentityUnitOfWork
from tests.fakes.security import FakePasswordHasher, FakeTokenHasher, FakeTokenIssuer

PASSWORD = "secureP@ss1!"


def build_use_case(
    *,
    uow: FakeIdentityUnitOfWork,
    password_hasher: FakePasswordHasher,
    token_issuer: FakeTokenIssuer,
    token_hasher: FakeTokenHasher,
    at_lifetime_minutes: int,
    rt_lifetime_days: int,
) -> LoginUseCase:
    """Собрать use case входа в систему из фейков."""
    return LoginUseCase(
        uow=uow,
        password_hasher=password_hasher,
        token_issuer=token_issuer,
        token_hasher=token_hasher,
        at_lifetime_minutes=at_lifetime_minutes,
        rt_lifetime_days=rt_lifetime_days,
    )


class TestLoginUseCaseSuccess:
    """Сценарии успешной аутентификации."""

    async def test_returns_tokens_and_creates_session(
        self,
        uow: FakeIdentityUnitOfWork,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Успешный вход: сессия создана, выпущена пара токенов."""
        identity = Identity.register(
            Username("john_doe"), password_hasher.hash(PASSWORD)
        )
        await uow.identity_repo.add(identity)

        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )
        result = await use_case.execute(
            LoginCommand(username="john_doe", password=PASSWORD)
        )

        assert result.access_token == f"token:{token_issuer.issued[1].token_id}"
        assert result.refresh_token == f"token:{token_issuer.issued[0].token_id}"

    async def test_session_contains_hashed_refresh_token(
        self,
        uow: FakeIdentityUnitOfWork,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """В сессии хранится хэш refresh-токена, а не сам токен."""
        identity = Identity.register(
            Username("john_doe"), password_hasher.hash(PASSWORD)
        )
        await uow.identity_repo.add(identity)

        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )
        await use_case.execute(LoginCommand(username="john_doe", password=PASSWORD))

        refresh_claims = token_issuer.issued[0]
        stored_session = uow.session_repo.added[0]

        assert stored_session.id == refresh_claims.session_id
        assert stored_session.identity_id == identity.id
        assert stored_session.session_secret == token_hasher.hash(
            result_refresh_token(token_issuer)
        )
        assert stored_session.expires_at == refresh_claims.expires_at

    async def test_claims_lifetimes_and_session_link(
        self,
        uow: FakeIdentityUnitOfWork,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Refresh-токен живёт дни, access — минуты; оба связаны одной сессией."""
        identity = Identity.register(
            Username("john_doe"), password_hasher.hash(PASSWORD)
        )
        await uow.identity_repo.add(identity)

        before = datetime.now(UTC)
        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )
        await use_case.execute(LoginCommand(username="john_doe", password=PASSWORD))
        after = datetime.now(UTC)

        refresh_claims = token_issuer.issued[0]
        access_claims = token_issuer.issued[1]

        assert refresh_claims.user_id == identity.id
        assert access_claims.user_id == identity.id
        assert refresh_claims.session_id == access_claims.session_id
        assert refresh_claims.expires_at == refresh_claims.issued_at + timedelta(
            days=rt_lifetime_days
        )
        assert access_claims.expires_at == access_claims.issued_at + timedelta(
            minutes=at_lifetime_minutes
        )
        assert before <= refresh_claims.issued_at <= after

    async def test_commits_unit_of_work(
        self,
        uow: FakeIdentityUnitOfWork,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Успешный сценарий завершается фиксацией транзакции."""
        identity = Identity.register(
            Username("john_doe"), password_hasher.hash(PASSWORD)
        )
        await uow.identity_repo.add(identity)

        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )
        await use_case.execute(LoginCommand(username="john_doe", password=PASSWORD))

        assert uow.commit_count == 1
        assert uow.rollback_count == 0


class TestLoginUseCaseFailures:
    """Сценарии неуспешной аутентификации."""

    async def test_unknown_user_raises_single_error(
        self,
        uow: FakeIdentityUnitOfWork,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Неизвестный пользователь получает единую ошибку без лишних вызовов."""
        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        with pytest.raises(IncorrectUsernameOrPasswordError) as exc_info:
            await use_case.execute(
                LoginCommand(username="unknown_user", password=PASSWORD)
            )

        assert str(exc_info.value) == "Incorrect username or password."
        assert token_issuer.issued == []
        assert uow.session_repo.added == []
        assert uow.rollback_count == 1

    async def test_wrong_password_raises_same_error(
        self,
        uow: FakeIdentityUnitOfWork,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Неверный пароль даёт ту же ошибку, что и неизвестный пользователь."""
        identity = Identity.register(
            Username("john_doe"), password_hasher.hash(PASSWORD)
        )
        await uow.identity_repo.add(identity)

        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        with pytest.raises(IncorrectUsernameOrPasswordError) as exc_info:
            await use_case.execute(
                LoginCommand(username="john_doe", password="wrong_password_1")
            )

        assert str(exc_info.value) == "Incorrect username or password."
        assert uow.session_repo.added == []

    async def test_invalid_username_raises_domain_error(
        self,
        uow: FakeIdentityUnitOfWork,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Username вне доменных инвариантов отклоняется use case."""
        command = LoginCommand.model_construct(username="ab", password=PASSWORD)
        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        with pytest.raises(InvalidUsernameLengthError):
            await use_case.execute(command)

    async def test_inactive_user_can_login(
        self,
        uow: FakeIdentityUnitOfWork,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Деактивированный пользователь получает токены.

        TODO(security): use case не проверяет ``identity.is_active`` — деактивированный
        пользователь может аутентифицироваться. Требуется решение разработчика:
        дефект или осознанное поведение (см. план тестирования).
        """
        identity = Identity.register(
            Username("john_doe"), password_hasher.hash(PASSWORD)
        )
        identity.deactivate()
        await uow.identity_repo.add(identity)

        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        result = await use_case.execute(
            LoginCommand(username="john_doe", password=PASSWORD)
        )

        assert result.access_token
        assert result.refresh_token


def result_refresh_token(token_issuer: FakeTokenIssuer) -> str:
    """Вычислить refresh-токен, возвращённый фейковым эмитентом."""
    return f"token:{token_issuer.issued[0].token_id}"
