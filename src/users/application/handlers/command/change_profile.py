from src.shared.application.exceptions import TokenRevokedError
from src.shared.application.ports.persistence import TokenBlacklist
from src.shared.application.ports.security import TokenVerifier
from src.shared.application.unset import is_set
from src.shared.domain.ports.messaging import EventDispatcher
from src.users.application.dto.commands import ChangeProfileCommand
from src.users.application.exceptions import (
    IdentityNotFoundError,
    NothingToUpdateError,
    ProfileNotFoundError,
)
from src.users.application.ports import UsersUnitOfWork
from src.users.domain.events import ProfileChangedEvent


class ChangeProfileCommandHandler:
    """Обработчик команды изменения профиля пользователя.

    Проверяет подлинность access-токена и его отсутствие в чёрном
    списке, загружает профиль пользователя и применяет только явно
    переданные изменения (поля, не равные ``UNSET``), после чего
    сохраняет их атомарно в рамках единицы работы. После успешной
    фиксации публикует доменное событие :class:`ProfileChangedEvent`
    для обновления производных представлений (read model).

    Parameters
    ----------
    uow : UsersUnitOfWork
        Единица работы, обеспечивающая атомарный доступ к репозиториям
        профилей и учётных записей.
    token_verifier : TokenVerifier
        Сервис проверки подлинности access-токенов и извлечения их
        утверждений.
    token_blacklist : TokenBlacklist
        Хранилище отозванных access-токенов.
    event_dispatcher : EventDispatcher
        Диспетчер доменных событий для публикации события изменения
        профиля после успешного коммита.
    """

    def __init__(
        self,
        uow: UsersUnitOfWork,
        token_verifier: TokenVerifier,
        token_blacklist: TokenBlacklist,
        event_dispatcher: EventDispatcher,
    ) -> None:
        self._uow = uow
        self._token_verifier = token_verifier
        self._token_blacklist = token_blacklist
        self._event_dispatcher = event_dispatcher

    async def execute(self, command: ChangeProfileCommand) -> None:
        """Изменить профиль пользователя.

        Применяет к профилю только те поля команды, которые были явно
        переданы (отличаются от ``UNSET``), сохраняет изменения
        с проверкой версии агрегата и публикует событие изменения
        профиля.

        Parameters
        ----------
        command : ChangeProfileCommand
            Объект с данными для изменения профиля, содержащий access-токен
            и обновляемые поля.

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
        NothingToUpdateError
            Если объект с данными не содержит ни одного обновляемого поля.
        ProfileNotFoundError
            Если профиль для учётной записи из токена не найден.
        IdentityNotFoundError
            Если учётная запись для профиля не найдена.
        ConcurrentModificationError
            Если версия профиля изменилась с момента загрузки.
        """
        claims = self._token_verifier.verify(command.access_token)

        if await self._token_blacklist.is_revoked(claims.token_id):
            raise TokenRevokedError("Passed access token has been revoked.")

        if not is_set(command.display_name) and not is_set(command.avatar_url):
            raise NothingToUpdateError(
                "No fields to update: provide display_name or avatar_url."
            )

        async with self._uow:
            profile = await self._uow.profiles.get_by_identity_id(claims.user_id)

            if profile is None:
                raise ProfileNotFoundError(
                    f"Profile for user {claims.user_id} not found."
                )

            identity = await self._uow.identities.get_by_id(claims.user_id)

            if identity is None:
                raise IdentityNotFoundError(f"Identity {claims.user_id} not found.")

            if is_set(command.display_name):
                profile.change_display_name(command.display_name)

            if is_set(command.avatar_url):
                profile.change_avatar_url(command.avatar_url)

            await self._uow.profiles.save_profile_changes(profile)

        await self._event_dispatcher.publish(
            ProfileChangedEvent(
                identity_id=identity.id,
                profile_id=profile.id,
                username=identity.username.value,
                display_name=profile.display_name.value,
                avatar_url=(
                    profile.avatar_url.value if profile.avatar_url is not None else None
                ),
            )
        )
