"""Unit-тесты :class:`RegisterUserUseCase`."""

import pytest

from src.identity.application.commands import RegisterUserCommand
from src.identity.application.use_cases import RegisterUserUseCase
from src.identity.domain.exceptions import UsernameAlreadyExistsError
from src.identity.domain.value_objects import Username
from tests.fakes.identity_uow import (
    FakeIdentityRepository,
    FakeIdentityUnitOfWork,
    FakeProfileRepository,
)
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
) -> RegisterUserUseCase:
    """Собрать use case регистрации из фейков."""
    return RegisterUserUseCase(
        uow=uow,
        password_hasher=password_hasher,
        token_issuer=token_issuer,
        token_hasher=token_hasher,
        at_lifetime_minutes=at_lifetime_minutes,
        rt_lifetime_days=rt_lifetime_days,
    )


def register_command(**overrides) -> RegisterUserCommand:
    """Создать команду регистрации со значениями по умолчанию."""
    defaults = {
        "username": "john_doe",
        "password": PASSWORD,
        "display_name": "John Doe",
    }
    defaults.update(overrides)
    return RegisterUserCommand(**defaults)


class TestRegisterUserUseCaseSuccess:
    """Сценарии успешной регистрации."""

    async def test_creates_identity_profile_and_session(
        self,
        uow: FakeIdentityUnitOfWork,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Регистрация создаёт учётную запись, профиль и сессию."""
        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        result = await use_case.execute(register_command())

        stored_identity = await uow.identity_repo.get_by_username(Username("john_doe"))  # type: ignore[union-attr]
        assert stored_identity is not None
        assert result.user_id == stored_identity.id
        assert stored_identity.is_active is True
        assert stored_identity.password_hash == password_hasher.hash(PASSWORD)

        profile = await uow.profile_repo.get_by_identity_id(stored_identity.id)  # type: ignore[union-attr]
        assert profile is not None
        assert profile.display_name.value == "John Doe"
        assert profile.avatar_url is None

        assert len(uow.session_repo.added) == 1
        assert uow.session_repo.added[0].identity_id == stored_identity.id

    async def test_password_hashed_exactly_once(
        self,
        uow: FakeIdentityUnitOfWork,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Пароль хешируется ровно один раз."""
        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        await use_case.execute(register_command())

        assert password_hasher.hash_calls == [PASSWORD]

    async def test_session_stores_hashed_refresh_token(
        self,
        uow: FakeIdentityUnitOfWork,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """В сессии хранится хэш refresh-токена, связанного с claims."""
        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        await use_case.execute(register_command())

        refresh_claims = token_issuer.issued[0]
        access_claims = token_issuer.issued[1]
        stored_session = uow.session_repo.added[0]

        assert stored_session.id == refresh_claims.session_id
        assert stored_session.session_secret == token_hasher.hash(
            f"token:{refresh_claims.token_id}"
        )
        assert access_claims.session_id == stored_session.id
        assert access_claims.user_id == refresh_claims.user_id

    async def test_returns_tokens(
        self,
        uow: FakeIdentityUnitOfWork,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Результат содержит выпущенные токены."""
        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        result = await use_case.execute(register_command())

        assert result.access_token == f"token:{token_issuer.issued[1].token_id}"
        assert result.refresh_token == f"token:{token_issuer.issued[0].token_id}"

    async def test_commits_unit_of_work(
        self,
        uow: FakeIdentityUnitOfWork,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Успешная регистрация фиксирует транзакцию."""
        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        await use_case.execute(register_command())

        assert uow.commit_count == 1
        assert uow.rollback_count == 0


class TestRegisterUserUseCaseFailures:
    """Сценарии неуспешной регистрации."""

    async def test_duplicate_username_propagates(
        self,
        uow: FakeIdentityUnitOfWork,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Дубликат username пробрасывается без добавления профиля и сессии."""
        await _seed_existing_user(uow, password_hasher)

        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        with pytest.raises(UsernameAlreadyExistsError):
            await use_case.execute(register_command())

        assert uow.profile_repo.added == []
        assert uow.session_repo.added == []
        assert token_issuer.issued == []
        assert uow.rollback_count == 1

    async def test_profiles_add_failure_rolls_back(
        self,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Сбой добавления профиля откатывает всю транзакцию."""
        profiles = FakeProfileRepository()
        profiles.fail_on_add = RuntimeError("database unavailable")

        uow = FakeIdentityUnitOfWork(profiles=profiles)
        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        with pytest.raises(RuntimeError, match="database unavailable"):
            await use_case.execute(register_command())

        assert uow.identity_repo.added == []
        assert uow.session_repo.added == []
        assert uow.rollback_count == 1
        assert uow.commit_count == 0

    async def test_identity_add_failure_rolls_back(
        self,
        password_hasher: FakePasswordHasher,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Сбой добавления учётной записи откатывает транзакцию."""
        identities = FakeIdentityRepository()
        identities.fail_on_add = RuntimeError("constraint violation")

        uow = FakeIdentityUnitOfWork(identities=identities)
        use_case = build_use_case(
            uow=uow,
            password_hasher=password_hasher,
            token_issuer=token_issuer,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        with pytest.raises(RuntimeError, match="constraint violation"):
            await use_case.execute(register_command())

        assert uow.rollback_count == 1
        assert uow.commit_count == 0


async def _seed_existing_user(
    uow: FakeIdentityUnitOfWork, password_hasher: FakePasswordHasher
) -> None:
    """Добавить в репозиторий пользователя с занятым username."""
    from src.identity.domain.entities import Identity

    identity = Identity.register(Username("john_doe"), password_hasher.hash(PASSWORD))
    await uow.identity_repo.add(identity)
