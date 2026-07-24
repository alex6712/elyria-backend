from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.identity.application.commands import RefreshSessionCommand
from src.identity.application.dto import TokenClaimsDTO
from src.identity.application.exceptions import SessionNotFoundError
from src.identity.application.ports import IdentityUnitOfWork
from src.identity.application.ports.security import (
    TokenHasher,
    TokenIssuer,
    TokenVerifier,
)
from src.identity.application.results import RefreshSessionResult


class RefreshSessionUseCase:
    """Use case обновления пары access/refresh токенов.

    Валидирует предоставленный refresh-токен, проверяет
    наличие и состояние соответствующей сессии в БД, ротирует
    секрет сессии (аннулирует старый refresh-токен) и выпускает
    новую пару JWT-токенов. Обновление происходит в рамках одной
    транзакции единицы работы для обеспечения атомарности.

    Parameters
    ----------
    uow : IdentityUnitOfWork
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
        uow: IdentityUnitOfWork,
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
        3. Проверяет, что сессия валидна и хеш переданного токена
           совпадает с сохранённым секретом сессии.
        4. Вычисляет время истечения новой сессии.
        5. Выпускает новый refresh-токен через ``TokenIssuer``.
        6. Вызывает ``session.rotate_secret()`` - метод доменной
           сущности, проверяющий доменные инварианты (сессия не
           отозвана и не истекла, согласно ADR-0005).
        7. Сохраняет изменения через ``sessions.save_rotation()``
           с проверкой версии агрегата (optimistic locking).
        8. Выпускает новый short-lived access-токен.

        В случае любой ошибки до коммита транзакция будет отменена
        благодаря использованию асинхронного контекст-менеджера
        единицы работы.

        Parameters
        ----------
        command : RefreshSessionCommand
            Команда, содержащая текущий refresh-токен пользователя.

        Returns
        -------
        RefreshSessionResult
            Результат операции, содержащий новые access и refresh токены.

        Raises
        ------
        SessionNotFoundError
            Если сессия с указанным ID отсутствует, была отозвана,
            истекла или сохранённый хеш секрета не соответствует
            хешу переданного токена (защита от кражи токена).
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
        async with self._uow:
            claims = self._token_verifier.verify(command.refresh_token)

            session = await self._uow.sessions.get_by_id(claims.session_id)
            if session is None:
                raise SessionNotFoundError("Session with passed id not found.")
            if session.session_secret != self._token_hasher.hash(command.refresh_token):
                raise SessionNotFoundError(
                    "Session with passed id and session secret not found."
                )

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

            session.rotate_secret(
                self._token_hasher.hash(new_refresh_token), refresh_expires_at, at=now
            )
            await self._uow.sessions.save_rotation(session)

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
