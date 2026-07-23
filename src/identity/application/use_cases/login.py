from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.identity.application.commands import LoginCommand
from src.identity.application.dto import TokenClaimsDTO
from src.identity.application.exceptions import IncorrectUsernameOrPasswordError
from src.identity.application.ports import IdentityUnitOfWork
from src.identity.application.ports.security import (
    PasswordHasher,
    TokenHasher,
    TokenIssuer,
)
from src.identity.application.results import LoginResult
from src.identity.domain.entities import Session
from src.identity.domain.value_objects import Username


class LoginUseCase:
    """Use case аутентификации пользователя.

    Выполняет проверку учётных данных пользователя (имя пользователя
    и пароль) и при успешной аутентификации создаёт новую сессию,
    выпуская access и refresh токены.

    Parameters
    ----------
    uow : IdentityUnitOfWork
        Единица работы, обеспечивающая атомарный доступ к репозиториям
        учётных записей, профилей и сессий.
    password_hasher : PasswordHasher
        Сервис хеширования паролей для проверки учётных данных.
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

    async def execute(self, command: LoginCommand) -> LoginResult:
        """Аутентифицировать пользователя и выпустить токены.

        Выполняет поиск учётной записи по имени пользователя,
        проверяет соответствие пароля, создаёт новую сессию
        и выпускает access и refresh токены.

        Parameters
        ----------
        command : LoginCommand
            Данные для входа: имя пользователя и пароль.

        Returns
        -------
        LoginResult
            Результат аутентификации с access и refresh токенами.

        Raises
        ------
        Exception
            Если пользователь с указанным именем не найден
            или пароль не соответствует сохранённому хешу.
        """
        async with self._uow:
            identity = await self._uow.identities.get_by_username(
                Username(command.username)
            )

            if identity is None or not self._password_hasher.verify(
                command.password, identity.password_hash
            ):
                raise IncorrectUsernameOrPasswordError(
                    "Incorrect username or password."
                )

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

            await self._uow.sessions.add(
                Session.issue(
                    id=session_id,
                    identity_id=identity.id,
                    session_secret=self._token_hasher.hash(refresh_token),
                    expires_at=refresh_expires_at,
                )
            )

            access_token = self._token_issuer.issue(
                TokenClaimsDTO(
                    user_id=identity.id,
                    expires_at=now + timedelta(minutes=self._at_lifetime_minutes),
                    issued_at=now,
                    token_id=uuid4(),
                    session_id=session_id,
                )
            )

        return LoginResult(access_token=access_token, refresh_token=refresh_token)
