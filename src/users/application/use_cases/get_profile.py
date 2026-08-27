from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.shared.application.exceptions import TokenRevokedError
from src.shared.application.ports.persistence import TokenBlacklist
from src.shared.application.ports.security import TokenVerifier
from src.users.application.exceptions import ProfileNotFoundError
from src.users.application.inputs import GetProfileInput
from src.users.application.ports import UsersUnitOfWork
from src.users.domain.value_objects import AvatarUrl, DisplayName


@dataclass(frozen=True, slots=True)
class _GetProfileResult:
    """Результат успешного получения профиля пользователя.

    Содержит отображаемые данные профиля, возвращаемые клиенту.
    Технические атрибуты агрегата (версия для optimistic locking,
    идентификатор учётной записи) в результат не включаются.

    Attributes
    ----------
    id : UUID
        Уникальный идентификатор профиля.
    display_name : DisplayName
        Value object с отображаемым именем профиля.
    avatar_url : AvatarUrl | None
        URL изображения аватара профиля либо ``None``, если аватар
        не установлен.
    created_at : datetime
        Дата и время создания профиля.
    updated_at : datetime | None
        Дата и время последнего изменения профиля либо ``None``,
        если профиль не изменялся после создания.
    """

    id: UUID
    display_name: DisplayName
    avatar_url: AvatarUrl | None
    created_at: datetime
    updated_at: datetime | None


class GetProfileUseCase:
    """Use case получения профиля пользователя.

    Проверяет подлинность access-токена и его отсутствие в чёрном
    списке, после чего возвращает профиль: либо указанной во входных
    данных учётной записи (просмотр чужого профиля), либо учётной
    записи владельца токена (сценарий "мой профиль").

    Parameters
    ----------
    uow : UsersUnitOfWork
        Единица работы, обеспечивающая доступ к репозиторию профилей.
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

    async def execute(self, input: GetProfileInput) -> _GetProfileResult:
        """Получить профиль пользователя.

        Проверяет access-токен и его отсутствие в чёрном списке,
        определяет целевой профиль (по переданному идентификатору
        либо по учётной записи владельца токена) и загружает его
        в рамках единицы работы. Читающая операция: изменений
        агрегата не выполняет, транзакция фиксируется без сохранения
        состояния.

        Parameters
        ----------
        input : GetProfileInput
            Объект с данными для получения профиля, содержащий
            access-токен и необязательный идентификатор профиля.

        Returns
        -------
        _GetProfileResult
            Отображаемые данные найденного профиля.

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
        ProfileNotFoundError
            Если профиль запрашиваемой учётной записи не найден.
        """
        claims = self._token_verifier.verify(input.access_token)

        if await self._token_blacklist.is_revoked(claims.token_id):
            raise TokenRevokedError("Passed access token has been revoked.")

        if input.profile_id is not None:
            return await self._get_by_profile_id(input.profile_id)

        return await self._get_by_identity_id(claims.user_id)

    async def _get_by_profile_id(self, profile_id: UUID) -> _GetProfileResult:
        """Получить профиль по идентификатору профиля.

        Выполняет поиск профиля по его уникальному идентификатору
        в рамках единицы работы.

        Parameters
        ----------
        profile_id : UUID
            Уникальный идентификатор профиля.

        Returns
        -------
        _GetProfileResult
            Отображаемые данные найденного профиля.

        Raises
        ------
        ProfileNotFoundError
            Если профиль с указанным идентификатором не найден.
        """
        async with self._uow:
            profile = await self._uow.profiles.get_by_id(profile_id)

            if profile is None:
                raise ProfileNotFoundError(f"Profile with id={profile_id} not found.")

            return _GetProfileResult(
                id=profile.id,
                display_name=profile.display_name,
                avatar_url=profile.avatar_url,
                created_at=profile.created_at,
                updated_at=profile.updated_at,
            )

    async def _get_by_identity_id(self, identity_id: UUID) -> _GetProfileResult:
        """Получить профиль по идентификатору учётной записи.

        Выполняет поиск профиля по идентификатору связанной учётной
        записи (внутренний идентификатор аутентификации). Используется
        для сценария "мой профиль", когда идентификатор профиля
        неизвестен, но доступен ``identity_id`` из access-токена.

        Parameters
        ----------
        identity_id : UUID
            Идентификатор учётной записи пользователя, извлечённый
            из утверждений ``sub`` access-токена.

        Returns
        -------
        _GetProfileResult
            Отображаемые данные найденного профиля.

        Raises
        ------
        ProfileNotFoundError
            Если профиль для указанной учётной записи не найден.
        """
        async with self._uow:
            profile = await self._uow.profiles.get_by_identity_id(identity_id)

            if profile is None:
                raise ProfileNotFoundError(
                    f"Profile with identity_id={identity_id} not found."
                )

            return _GetProfileResult(
                id=profile.id,
                display_name=profile.display_name,
                avatar_url=profile.avatar_url,
                created_at=profile.created_at,
                updated_at=profile.updated_at,
            )
