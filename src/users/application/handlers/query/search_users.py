from src.shared.application.exceptions import TokenRevokedError
from src.shared.application.ports.persistence import TokenBlacklist
from src.shared.application.ports.security import TokenVerifier
from src.users.application.dto.queries import SearchUsersQuery
from src.users.application.dto.results import SearchUsersResult
from src.users.application.ports import UsersUnitOfWork


class SearchUsersQueryHandler:
    """Query handler нечёткого поиска учётных записей по имени пользователя.

    Проверяет подлинность access-токена и его отсутствие в чёрном
    списке, после чего выполняет поиск по подстроке имени пользователя
    в read model в рамках единицы работы. Возвращает данные
    учётной записи (Identity) и связанного профиля (Profile) с применением
    пагинации.

    Parameters
    ----------
    uow : UsersUnitOfWork
        Единица работы, обеспечивающая доступ к репозиторию read model
        поиска пользователей по имени пользователя.
    token_verifier : TokenVerifier
        Сервис проверки подлинности access-токенов и извлечения их
        утверждений.
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

    async def execute(self, query: SearchUsersQuery) -> SearchUsersResult:
        """Выполнить нечёткий поиск учётных записей по имени пользователя.

        Проверяет access-токен, ищет подстроку имени пользователя
        в read model с применением пагинации и возвращает найденные
        строки read model вместе с общим количеством результатов.

        Parameters
        ----------
        query : SearchUsersQuery
            Объект с данными для поиска, содержащий access-токен,
            подстроку имени пользователя и параметры пагинации.

        Returns
        -------
        SearchUsersResult
            Найденные строки read model и общее количество результатов.

        Raises
        ------
        TokenExpiredError
            Если срок действия access-токена истёк.
        TokenSignatureInvalidError
            Если подпись access-токена не прошла проверку.
        TokenInvalidError
            Если в access-токене отсутствуют обязательные утверждения
            либо токен имеет некорректный формат.
        TokenRevokedError
            Если access-токен был отозван и находится в чёрном списке.
        """
        claims = self._token_verifier.verify(query.access_token)

        if await self._token_blacklist.is_revoked(claims.token_id):
            raise TokenRevokedError("Passed access token has been revoked.")

        async with self._uow:
            total = await self._uow.user_search.count_by_username(query.query)
            items = await self._uow.user_search.search_by_username(
                query.query, query.limit, query.offset
            )

        return SearchUsersResult(items=items, total=total)
