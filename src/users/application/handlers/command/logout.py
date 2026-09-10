from src.shared.application.ports.persistence import TokenBlacklist
from src.shared.application.ports.security import TokenVerifier
from src.users.application.dto.commands import LogoutCommand
from src.users.application.ports import UsersUnitOfWork


class LogoutCommandHandler:
    """Обработчик команды завершения пользовательской сессии.

    Выполняет отзыв access-токена и, если соответствующая сессия существует,
    помечает её как отозванную. Операция является идемпотентной: отсутствие
    сессии не считается ошибкой.

    Parameters
    ----------
    uow : UsersUnitOfWork
        Единица работы, обеспечивающая атомарный доступ к репозиторию
        сессий.
    token_verifier : TokenVerifier
        Сервис проверки подлинности access-токенов и извлечения их утверждений.
    token_blacklist : TokenBlacklist
        Хранилище отозванных access-токенов.
    """

    def __init__(
        self,
        uow: UsersUnitOfWork,
        token_verifier: TokenVerifier,
        token_blacklist: TokenBlacklist,
    ) -> None:
        self._uow = uow
        self._token_verifier = token_verifier
        self._token_blacklist = token_blacklist

    async def execute(self, command: LogoutCommand) -> None:
        """Завершить пользовательскую сессию.

        Проверяет подлинность access-токена, добавляет его идентификатор
        в список отозванных токенов и, если связанная с ним сессия существует,
        помечает её как отозванную.

        Parameters
        ----------
        command : LogoutCommand
            Данные для завершения сессии, содержащие access-токен.

        Raises
        ------
        TokenExpiredError
            Если срок действия токена истёк.
        TokenSignatureInvalidError
            Если подпись токена не прошла проверку.
        TokenInvalidError
            Если в токене отсутствуют обязательные утверждения
            либо токен имеет некорректный формат.
        """
        claims = self._token_verifier.verify(command.access_token)

        await self._token_blacklist.revoke(claims.token_id, claims.expires_at)

        async with self._uow:
            session = await self._uow.sessions.get_by_id(claims.session_id)
            if session is None:
                return

            session.revoke()

            await self._uow.sessions.save_revocation(session)
