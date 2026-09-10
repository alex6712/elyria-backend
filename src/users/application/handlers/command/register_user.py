from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.shared.application.dto import TokenClaimsDTO
from src.shared.domain.ports.messaging import EventDispatcher
from src.users.application.dto.commands import RegisterUserCommand
from src.users.application.dto.results import RegisterUserResult
from src.users.application.exceptions import CompromisedPasswordError
from src.users.application.ports import UsersUnitOfWork
from src.users.application.ports.security import (
    CompromisedPasswordChecker,
    PasswordHasher,
    TokenHasher,
    TokenIssuer,
)
from src.users.domain.entities import Identity, Profile, Session
from src.users.domain.events import UserRegisteredEvent


class RegisterUserCommandHandler:
    """Обработчик команды регистрации нового пользователя.

    Создаёт учётную запись (Identity), профиль (Profile) и
    начальную сессию (Session), после чего выпускает access-
    и refresh-токены. После успешного коммита публикует доменное
    событие :class:`UserRegisteredEvent` для обновления производных
    представлений (read model).

    В сессии сохраняется только криптографический хеш
    refresh-токена. Сам токен возвращается пользователю и
    больше не хранится в открытом виде.

    Parameters
    ----------
    uow : UsersUnitOfWork
        Единица работы с вложенными репозиториями.
    password_hasher : PasswordHasher
        Сервис хеширования паролей.
    compromised_password_checker : CompromisedPasswordChecker
        Сервис проверки пароля на утечки данных.
    token_issuer : TokenIssuer
        Сервис выпуска новых токенов.
    token_hasher : TokenHasher
        Сервис криптографического хеширования сырых токенов.
    event_dispatcher : EventDispatcher
        Диспетчер доменных событий для публикации события регистрации
        пользователя после успешного коммита.
    at_lifetime_minutes : int
        Время жизни выдаваемого access-токена в минутах.
    rt_lifetime_days : int
        Время жизни выдаваемого refresh-токена и связанной с ним сессии в днях.
    """

    def __init__(
        self,
        uow: UsersUnitOfWork,
        password_hasher: PasswordHasher,
        compromised_password_checker: CompromisedPasswordChecker,
        token_issuer: TokenIssuer,
        token_hasher: TokenHasher,
        event_dispatcher: EventDispatcher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        self._uow = uow
        self._password_hasher = password_hasher
        self._compromised_password_checker = compromised_password_checker
        self._token_issuer = token_issuer
        self._token_hasher = token_hasher
        self._event_dispatcher = event_dispatcher
        self._at_lifetime_minutes = at_lifetime_minutes
        self._rt_lifetime_days = rt_lifetime_days

    async def execute(self, command: RegisterUserCommand) -> RegisterUserResult:
        """Зарегистрировать нового пользователя.

        Создаёт учётную запись, профиль и начальную пользовательскую
        сессию, затем выпускает access- и refresh-токены и публикует
        событие регистрации.

        Parameters
        ----------
        command : RegisterUserCommand
            Данные для регистрации пользователя.

        Returns
        -------
        RegisterUserResult
            Идентификаторы созданных учётной записи и профиля,
            а также выпущенные access- и refresh-токены.

        Raises
        ------
        CompromisedPasswordError
            Если пароль встречается в известных утечках данных.
        UsernameAlreadyExistsError
            Если пользователь с указанным именем уже существует.
        """
        if await self._compromised_password_checker.is_compromised(command.password):
            raise CompromisedPasswordError(
                "Password has been compromised and cannot be used."
            )

        identity = Identity.register(
            command.username, self._password_hasher.hash(command.password)
        )

        async with self._uow:
            await self._uow.identities.add(identity)

            profile = Profile.create(identity.id, command.display_name)

            now = datetime.now(UTC)
            refresh_expires_at = now + timedelta(days=self._rt_lifetime_days)

            refresh_token = self._token_issuer.issue(
                TokenClaimsDTO(
                    user_id=identity.id,
                    expires_at=refresh_expires_at,
                    issued_at=now,
                    token_id=uuid4(),
                    session_id=(session_id := uuid4()),
                )
            )

            session = Session.issue(
                id=session_id,
                identity_id=identity.id,
                session_secret=self._token_hasher.hash(refresh_token),
                expires_at=refresh_expires_at,
            )

            await self._uow.profiles.add(profile)
            await self._uow.sessions.add(session)

            access_token = self._token_issuer.issue(
                TokenClaimsDTO(
                    user_id=identity.id,
                    expires_at=now + timedelta(minutes=self._at_lifetime_minutes),
                    issued_at=now,
                    token_id=uuid4(),
                    session_id=session.id,
                )
            )

        await self._event_dispatcher.publish(
            UserRegisteredEvent(
                identity_id=identity.id,
                profile_id=profile.id,
                username=command.username.value,
                display_name=command.display_name.value,
                avatar_url=(
                    profile.avatar_url.value if profile.avatar_url is not None else None
                ),
            )
        )

        return RegisterUserResult(
            identity_id=identity.id,
            profile_id=profile.id,
            access_token=access_token,
            refresh_token=refresh_token,
        )
