from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.identity.application.commands import RegisterUserCommand
from src.identity.application.dto import TokenClaimsDTO
from src.identity.application.ports import IdentityUnitOfWork
from src.identity.application.ports.security import (
    PasswordHasher,
    TokenHasher,
    TokenIssuer,
)
from src.identity.application.results import RegisterUserResult
from src.identity.domain.entities import Identity, Profile, Session
from src.identity.domain.value_objects import DisplayName, Username


class RegisterUserUseCase:
    """Use case регистрации нового пользователя.

    Создаёт учётную запись (Identity), профиль (Profile) и
    начальную сессию (Session), после чего выпускает access-
    и refresh-токены.

    В сессии сохраняется только криптографический хеш
    refresh-токена. Сам токен возвращается пользователю и
    больше не хранится в открытом виде.

    Parameters
    ----------
    uow : IdentityUnitOfWork
        Единица работы с вложенными репозиториями.
    password_hasher : PasswordHasher
        Сервис хеширования паролей.
    token_issuer : TokenIssuer
        Сервис выпуска новых токенов.
    token_hasher : TokenHasher
        Сервис криптографического хеширования сырых токенов.
    at_lifetime_minutes : int
        Время жизни выдаваемого access-токена в минутах.
    rt_lifetime_days : int
        Время жизни выдаваемого refresh-токена и связанной с ним сессии в днях.
    """

    def __init__(
        self,
        uow: IdentityUnitOfWork,
        password_hasher: PasswordHasher,
        token_issuer: TokenIssuer,
        token_hasher: TokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        self._uow = uow
        self._password_hasher = password_hasher
        self._token_issuer = token_issuer
        self._token_hasher = token_hasher
        self._at_lifetime_minutes = at_lifetime_minutes
        self._rt_lifetime_days = rt_lifetime_days

    async def execute(self, command: RegisterUserCommand) -> RegisterUserResult:
        """Зарегистрировать нового пользователя.

        Создаёт учётную запись, профиль и начальную пользовательскую
        сессию, затем выпускает access- и refresh-токены.

        Parameters
        ----------
        command : RegisterUserCommand
            Данные для регистрации пользователя.

        Returns
        -------
        RegisterUserResult
            Идентификатор созданного пользователя и выпущенные
            access- и refresh-токены.

        Raises
        ------
        UsernameAlreadyExistsError
            Если пользователь с указанным именем уже существует.
        """
        async with self._uow:
            identity = Identity.register(
                Username(command.username), self._password_hasher.hash(command.password)
            )

            await self._uow.identities.add(identity)

            profile = Profile.create(identity.id, DisplayName(command.display_name))

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

        return RegisterUserResult(
            user_id=identity.id, access_token=access_token, refresh_token=refresh_token
        )
