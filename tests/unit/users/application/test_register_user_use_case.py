"""Unit-тесты ``RegisterUserCommandHandler``."""

import pytest

from src.shared.application.dto import TokenClaimsDTO
from src.users.application.dto.commands import RegisterUserCommand
from src.users.application.exceptions import CompromisedPasswordError
from src.users.application.handlers.command.register_user import (
    RegisterUserCommandHandler,
)
from src.users.domain.events import UserRegisteredEvent
from src.users.domain.exceptions import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from src.users.domain.value_objects import DisplayName, Email, Password, Username
from tests.fakes.identity_uow import FakeUsersUnitOfWork
from tests.fakes.security import (
    FakeCompromisedPasswordChecker,
    FakePasswordHasher,
    FakeTokenHasher,
    FakeTokenIssuer,
)

_VALID_PASSWORD = "VeryStrongP@ssw0rd123!"
_DEFAULT_USERNAME = Username("john_doe")
_DEFAULT_EMAIL = Email("john@example.com")
_DEFAULT_PASSWORD = Password(_VALID_PASSWORD)
_DEFAULT_DISPLAY_NAME = DisplayName("John Doe")


class FakeEventDispatcher:
    """Фейк диспетчера событий, записывающий опубликованные события."""

    def __init__(self) -> None:
        self.published: list[object] = []

    async def subscribe(self, event_type: object, handler: object) -> None:
        pass

    async def publish(self, event: object) -> None:
        self.published.append(event)


def build_handler(
    *,
    uow: FakeUsersUnitOfWork,
    password_hasher: FakePasswordHasher,
    compromised_checker: FakeCompromisedPasswordChecker,
    token_issuer: FakeTokenIssuer,
    token_hasher: FakeTokenHasher,
    event_dispatcher: FakeEventDispatcher,
) -> RegisterUserCommandHandler:
    """Собрать ``RegisterUserCommandHandler`` с фейками."""
    return RegisterUserCommandHandler(
        uow=uow,
        password_hasher=password_hasher,
        compromised_password_checker=compromised_checker,
        token_issuer=token_issuer,
        token_hasher=token_hasher,
        event_dispatcher=event_dispatcher,
        at_lifetime_minutes=15,
        rt_lifetime_days=30,
    )


def make_command(
    *,
    username: Username = _DEFAULT_USERNAME,
    email: Email = _DEFAULT_EMAIL,
    password: Password = _DEFAULT_PASSWORD,
    display_name: DisplayName = _DEFAULT_DISPLAY_NAME,
) -> RegisterUserCommand:
    """Создать ``RegisterUserCommand`` с переопределениями."""
    return RegisterUserCommand(
        username=username,
        email=email,
        password=password,
        display_name=display_name,
    )


class TestRegisterUserUseCaseSuccess:
    """Успешная регистрация пользователя."""

    async def test_creates_identity_with_email(self) -> None:
        uow = FakeUsersUnitOfWork()
        handler = build_handler(
            uow=uow,
            password_hasher=FakePasswordHasher(),
            compromised_checker=FakeCompromisedPasswordChecker(),
            token_issuer=FakeTokenIssuer(),
            token_hasher=FakeTokenHasher(),
            event_dispatcher=FakeEventDispatcher(),
        )

        _ = await handler.execute(make_command())

        [identity] = uow.identities.added
        assert identity.email.value == "john@example.com"
        assert identity.email_verified is False

    async def test_hashes_password_exactly_once(self) -> None:
        password_hasher = FakePasswordHasher()
        handler = build_handler(
            uow=FakeUsersUnitOfWork(),
            password_hasher=password_hasher,
            compromised_checker=FakeCompromisedPasswordChecker(),
            token_issuer=FakeTokenIssuer(),
            token_hasher=FakeTokenHasher(),
            event_dispatcher=FakeEventDispatcher(),
        )

        _ = await handler.execute(make_command())

        assert len(password_hasher.hash_calls) == 1

    async def test_issues_both_tokens(self) -> None:
        token_issuer = FakeTokenIssuer()
        handler = build_handler(
            uow=FakeUsersUnitOfWork(),
            password_hasher=FakePasswordHasher(),
            compromised_checker=FakeCompromisedPasswordChecker(),
            token_issuer=token_issuer,
            token_hasher=FakeTokenHasher(),
            event_dispatcher=FakeEventDispatcher(),
        )

        _ = await handler.execute(make_command())

        assert len(token_issuer.issued) == 2
        assert all(isinstance(c, TokenClaimsDTO) for c in token_issuer.issued)

    async def test_commits_unit_of_work(self) -> None:
        uow = FakeUsersUnitOfWork()
        handler = build_handler(
            uow=uow,
            password_hasher=FakePasswordHasher(),
            compromised_checker=FakeCompromisedPasswordChecker(),
            token_issuer=FakeTokenIssuer(),
            token_hasher=FakeTokenHasher(),
            event_dispatcher=FakeEventDispatcher(),
        )

        _ = await handler.execute(make_command())

        assert uow.commit_count == 1
        assert uow.rollback_count == 0

    async def test_publishes_user_registered_event(self) -> None:
        dispatcher = FakeEventDispatcher()
        handler = build_handler(
            uow=FakeUsersUnitOfWork(),
            password_hasher=FakePasswordHasher(),
            compromised_checker=FakeCompromisedPasswordChecker(),
            token_issuer=FakeTokenIssuer(),
            token_hasher=FakeTokenHasher(),
            event_dispatcher=dispatcher,
        )

        result = await handler.execute(make_command())

        assert len(dispatcher.published) == 1
        event = dispatcher.published[0]
        assert isinstance(event, UserRegisteredEvent)
        assert event.identity_id == result.identity_id
        assert event.username == "john_doe"

    async def test_returns_result_with_ids(self) -> None:
        uow = FakeUsersUnitOfWork()
        handler = build_handler(
            uow=uow,
            password_hasher=FakePasswordHasher(),
            compromised_checker=FakeCompromisedPasswordChecker(),
            token_issuer=FakeTokenIssuer(),
            token_hasher=FakeTokenHasher(),
            event_dispatcher=FakeEventDispatcher(),
        )

        result = await handler.execute(make_command())

        assert result.identity_id is not None
        assert result.profile_id is not None
        assert isinstance(result.access_token, str)
        assert isinstance(result.refresh_token, str)


class TestRegisterUserUseCaseFailures:
    """Ошибки при регистрации пользователя."""

    async def test_duplicate_email_propagates_and_rolls_back(self) -> None:
        uow = FakeUsersUnitOfWork()
        handler = build_handler(
            uow=uow,
            password_hasher=FakePasswordHasher(),
            compromised_checker=FakeCompromisedPasswordChecker(),
            token_issuer=FakeTokenIssuer(),
            token_hasher=FakeTokenHasher(),
            event_dispatcher=FakeEventDispatcher(),
        )

        _ = await handler.execute(make_command())

        with pytest.raises(EmailAlreadyExistsError):
            _ = await handler.execute(make_command(username=Username("another_user")))

        assert uow.rollback_count == 1
        assert [i.username.value for i in uow.identities.added] == ["john_doe"]

    async def test_duplicate_username_propagates_and_rolls_back(self) -> None:
        uow = FakeUsersUnitOfWork()
        handler = build_handler(
            uow=uow,
            password_hasher=FakePasswordHasher(),
            compromised_checker=FakeCompromisedPasswordChecker(),
            token_issuer=FakeTokenIssuer(),
            token_hasher=FakeTokenHasher(),
            event_dispatcher=FakeEventDispatcher(),
        )

        _ = await handler.execute(make_command())

        with pytest.raises(UsernameAlreadyExistsError):
            _ = await handler.execute(make_command(email=Email("other@example.com")))

        assert uow.rollback_count == 1
        assert [i.username.value for i in uow.identities.added] == ["john_doe"]

    async def test_compromised_password_aborts(self) -> None:
        checker = FakeCompromisedPasswordChecker()
        checker.is_compromised_result = True

        uow = FakeUsersUnitOfWork()
        handler = build_handler(
            uow=uow,
            password_hasher=FakePasswordHasher(),
            compromised_checker=checker,
            token_issuer=FakeTokenIssuer(),
            token_hasher=FakeTokenHasher(),
            event_dispatcher=FakeEventDispatcher(),
        )

        with pytest.raises(CompromisedPasswordError):
            _ = await handler.execute(make_command())

        assert uow.identities.added == []
        assert uow.rollback_count == 0  # прервано до входа в UoW
