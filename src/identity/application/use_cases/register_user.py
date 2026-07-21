from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.identity.application.commands import RegisterCommand
from src.identity.application.dto import TokenClaimsDTO
from src.identity.application.ports.persistence import (
    IdentityRepository,
    ProfileRepository,
    SessionRepository,
)
from src.identity.application.ports.security import (
    PasswordHasher,
    TokenHasher,
    TokenIssuer,
)
from src.identity.application.results import RegisterResult
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
    identity_repo : IdentityRepository
        Репозиторий учётных записей.
    profile_repo : ProfileRepository
        Репозиторий профилей.
    session_repo : SessionRepository
        Репозиторий пользовательских сессий.
    password_hasher : PasswordHasher
        Сервис хеширования паролей.
    token_issuer : TokenIssuer
        Сервис выпуска JWT-токенов.
    token_hasher : TokenHasher
        Сервис криптографического хеширования токенов.
    access_token_lifetime_minutes : int
        Время жизни access-токена в минутах.
    refresh_token_lifetime_days : int
        Время жизни refresh-токена и пользовательской сессии в днях.
    """

    def __init__(
        self,
        identity_repo: IdentityRepository,
        profile_repo: ProfileRepository,
        session_repo: SessionRepository,
        password_hasher: PasswordHasher,
        token_issuer: TokenIssuer,
        token_hasher: TokenHasher,
        hmac_secret_key: str,
        access_token_lifetime_minutes: int,
        refresh_token_lifetime_days: int,
    ) -> None:
        self._identity_repo = identity_repo
        self._profile_repo = profile_repo
        self._session_repo = session_repo
        self._password_hasher = password_hasher
        self._token_issuer = token_issuer
        self._token_hasher = token_hasher
        self._hmac_secret_key = hmac_secret_key
        self._access_token_lifetime_minutes = access_token_lifetime_minutes
        self._refresh_token_lifetime_days = refresh_token_lifetime_days

    async def execute(self, request: RegisterCommand) -> RegisterResult:
        """Зарегистрировать нового пользователя.

        Создаёт учётную запись, профиль и начальную пользовательскую
        сессию, затем выпускает access- и refresh-токены.

        Parameters
        ----------
        request : RegisterCommand
            Данные для регистрации пользователя.

        Returns
        -------
        RegisterResult
            Идентификатор созданного пользователя и выпущенные
            access- и refresh-токены.

        Raises
        ------
        UsernameAlreadyExistsError
            Если пользователь с указанным именем уже существует.
        """
        identity = Identity.register(
            Username(request.username), self._password_hasher.hash(request.password)
        )

        await self._identity_repo.add(identity)

        profile = Profile.create(identity.id, DisplayName(request.display_name))

        now = datetime.now(UTC)
        refresh_expires_at = now + timedelta(days=self._refresh_token_lifetime_days)

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

        await self._profile_repo.add(profile)
        await self._session_repo.add(session)

        access_token = self._token_issuer.issue(
            TokenClaimsDTO(
                user_id=identity.id,
                expires_at=now + timedelta(minutes=self._access_token_lifetime_minutes),
                issued_at=now,
                token_id=uuid4(),
                session_id=session.id,
            )
        )

        return RegisterResult(
            user_id=identity.id, access_token=access_token, refresh_token=refresh_token
        )
