from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.shared.application.dto import TokenClaimsDTO
from src.shared.application.ports.security import TokenVerifier
from src.users.application.dto.commands import RefreshSessionCommand
from src.users.application.dto.results import RefreshSessionResult
from src.users.application.exceptions import SessionNotFoundError
from src.users.application.ports import UsersUnitOfWork
from src.users.application.ports.security import TokenHasher, TokenIssuer
from src.users.domain.exceptions import InactiveUserError


class RefreshSessionCommandHandler:
    """Обработчик команды обновления пары access/refresh токенов.

    Валидирует предоставленный refresh-токен, проверяет
    наличие и состояние соответствующей сессии в БД, ротирует
    секрет сессии (аннулирует старый refresh-токен) и выпускает
    новую пару JWT-токенов. Обновление происходит в рамках одной
    транзакции единицы работы для обеспечения атомарности.

    Parameters
    ----------
    uow : UsersUnitOfWork
        Единица работы, обеспечивающая атомарный доступ к репозиторию сессий.
    token_issuer : TokenIssuer
        Сервис выпуска новых токенов.
    token_verifier : TokenVerifier
        Сервис проверки структуры, подписи и срока действия входящего токена.
    token_hasher : TokenHasher
        Сервис криптографического хеширования сырых токенов.
    at_lifetime_minutes : int
        Время жизни выдаваемого access-токена в минутах.
    rt_lifetime_days : int
        Время жизни выдаваемого refresh-токена и связанной с ним сессии в днях.
    """

    def __init__(
        self,
        uow: UsersUnitOfWork,
        token_issuer: TokenIssuer,
        token_verifier: TokenVerifier,
        token_hasher: TokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        self._uow = uow
        self._token_issuer = token_issuer
        self._token_verifier = token_verifier
        self._token_hasher = token_hasher
        self._at_lifetime_minutes = at_lifetime_minutes
        self._rt_lifetime_days = rt_lifetime_days

    async def execute(self, command: RefreshSessionCommand) -> RefreshSessionResult:
        """Обновить access и refresh токены по валидному refresh-токену.

        Алгоритм выполнения:
        1. Проверяет структуру и подпись переданного refresh-токена
           через ``TokenVerifier``.
        2. Загружает сессию по идентификатору из claims токена.
        3. Проверяет, что хеш переданного токена совпадает с сохранённым
           секретом сессии (защита от кражи токена).
        4. Проверяет, что учётная запись владельца сессии активна.
        5. Вычисляет время истечения новой сессии.
        6. Выпускает новый refresh-токен через ``TokenIssuer``.
        7. Вызывает ``session.refresh()`` - метод доменной
           сущности, проверяющий доменные инварианты (сессия не
           отозвана и не истекла, согласно ADR-0005).
        8. Сохраняет изменения через ``sessions.save_refresh()``
           с проверкой версии агрегата (optimistic locking).
        9. Выпускает новый short-lived access-токен.

        В случае любой ошибки до коммита транзакция будет отменена
        благодаря использованию асинхронного контекст-менеджера
        единицы работы.

        Parameters
        ----------
        command : RefreshSessionCommand
            Объект с данными, содержащий текущий refresh-токен пользователя.

        Returns
        -------
        RefreshSessionResult
            Результат операции, содержащий новые access и refresh токены.

        Raises
        ------
        SessionNotFoundError
            Если сессия с указанным ID отсутствует или сохранённый хеш
            секрета не соответствует хешу переданного токена (защита
            от кражи токена).
        SessionRevokedError
            Если сессия была отозвана.
        SessionExpiredError
            Если срок действия сессии истёк, даже если переданный
            refresh-токен ещё действителен.
        InactiveUserError
            Если учётная запись владельца сессии деактивирована.
        TokenExpiredError
            Если срок действия токена истёк.
        TokenSignatureInvalidError
            Если подпись токена не прошла проверку.
        TokenInvalidError
            Если в токене отсутствуют обязательные утверждения
            либо токен имеет некорректный формат.
        ConcurrentModificationError
            Если другой concurrent запрос изменил сессию между
            её загрузкой и сохранением (пробрасывается на уровень
            представления как 409 Conflict).
        """
        claims = self._token_verifier.verify(command.refresh_token)

        async with self._uow:
            session = await self._uow.sessions.get_by_id(claims.session_id)

            if session is None:
                raise SessionNotFoundError("Session with passed id not found.")

            if session.session_secret != self._token_hasher.hash(command.refresh_token):
                raise SessionNotFoundError(
                    "Session with passed id and session secret not found."
                )

            identity = await self._uow.identities.get_by_id(session.identity_id)

            if identity is None:
                raise SessionNotFoundError("Identity for session not found.")

            if not identity.is_active:
                raise InactiveUserError(identity.id)

            now = datetime.now(UTC)
            refresh_expires_at = now + timedelta(days=self._rt_lifetime_days)

            new_refresh_token = self._token_issuer.issue(
                TokenClaimsDTO(
                    user_id=claims.user_id,
                    expires_at=refresh_expires_at,
                    issued_at=now,
                    token_id=uuid4(),
                    session_id=claims.session_id,
                )
            )

            session.refresh(
                self._token_hasher.hash(new_refresh_token), refresh_expires_at, at=now
            )
            await self._uow.sessions.save_refresh(session)

            access_token = self._token_issuer.issue(
                TokenClaimsDTO(
                    user_id=claims.user_id,
                    expires_at=now + timedelta(minutes=self._at_lifetime_minutes),
                    issued_at=now,
                    token_id=uuid4(),
                    session_id=claims.session_id,
                )
            )

        return RefreshSessionResult(
            access_token=access_token, refresh_token=new_refresh_token
        )
