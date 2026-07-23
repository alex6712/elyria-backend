from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.identity.application.commands import RefreshCommand
from src.identity.application.dto import TokenClaimsDTO
from src.identity.application.exceptions import SessionNotFoundError
from src.identity.application.ports import IdentityUnitOfWork
from src.identity.application.ports.security import (
    TokenHasher,
    TokenIssuer,
    TokenVerifier,
)
from src.identity.application.results import RefreshResult


class RefreshUseCase:
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

    async def execute(self, command: RefreshCommand) -> RefreshResult:
        """Обновить access и refresh токены по валидному refresh-токену.

        Алгоритм выполнения:
        1. Проверяет структуру и подпись переданного refresh-токена
           через `TokenVerifier`.
        2. Вычисляет время истечения новой сессии.
        3. Выпускает новый refresh-токен через `TokenIssuer` с
           обновленным идентификатором токена.
        4. Вызывает ротацию секрета сессии в хранилище (`sessions.rotate_secret`).
           Если сессия не найдена или её текущий сохраненный хеш не совпадает с
           хешем переданного токена, выбрасывается `SessionNotFoundError`.
           Это защищает от повторного использования отозванных токенов.
        5. Выпускает новый short-lived access-токен.

        В случае любой ошибки до коммита контекста транзакция будет отменена благодаря
        использованию асинхронного контекст-менеджера единицы работы.

        Parameters
        ----------
        command : RefreshCommand
            Команда, содержащая текущий refresh-токен пользователя.

        Returns
        -------
        RefreshResult
            Результат операции, содержащий новые access и refresh токены.

        Raises
        ------
        SessionNotFoundError
            Если сессия с указанным ID отсутствует, была отозвана или сохраненный
            хеш секрета не соответствует переданному токену (защита от кражи токена).
        TokenExpiredError
            Если срок действия токена истёк.
        TokenSignatureInvalidError
            Если подпись токена не прошла проверку.
        TokenInvalidError
            Если в токене отсутствуют обязательные утверждения
            либо токен имеет некорректный формат.
        """
        async with self._uow:
            claims = self._token_verifier.verify(command.refresh_token)

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

            refreshed = await self._uow.sessions.rotate_secret(
                claims.session_id,
                self._token_hasher.hash(command.refresh_token),
                self._token_hasher.hash(new_refresh_token),
                refresh_expires_at,
            )
            if not refreshed:
                raise SessionNotFoundError(
                    "Session with passed id and session secret not found."
                )

            access_token = self._token_issuer.issue(
                TokenClaimsDTO(
                    user_id=claims.user_id,
                    expires_at=now + timedelta(minutes=self._at_lifetime_minutes),
                    issued_at=now,
                    token_id=uuid4(),
                    session_id=claims.session_id,
                )
            )

        return RefreshResult(access_token=access_token, refresh_token=new_refresh_token)
