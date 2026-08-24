from src.shared.application.exceptions import TokenRevokedError
from src.shared.application.ports.persistence import TokenBlacklist
from src.shared.application.ports.security import TokenVerifier
from src.shared.application.unset import is_set
from src.users.application.commands import ChangeProfileCommand
from src.users.application.exceptions import NothingToUpdateError, ProfileNotFoundError
from src.users.application.ports import UsersUnitOfWork


class ChangeProfileUseCase:
    """Use case изменения профиля пользователя.

    Проверяет подлинность access-токена и его отсутствие в чёрном
    списке, загружает профиль пользователя и применяет только явно
    переданные изменения (поля, не равные ``UNSET``), после чего
    сохраняет их атомарно в рамках единицы работы.

    Parameters
    ----------
    uow : UsersUnitOfWork
        Единица работы, обеспечивающая атомарный доступ к репозиторию
        профилей.
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

    async def execute(self, command: ChangeProfileCommand) -> None:
        """Изменить профиль пользователя.

        Применяет к профилю только те поля команды, которые были явно
        переданы (отличаются от ``UNSET``), и сохраняет изменения
        с проверкой версии агрегата.

        Parameters
        ----------
        command : ChangeProfileCommand
            Команда на изменение профиля, содержащая access-токен
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
            Если команда не содержит ни одного обновляемого поля.
        ProfileNotFoundError
            Если профиль для учётной записи из токена не найден.
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

            if is_set(command.display_name):
                profile.change_display_name(command.display_name)

            if is_set(command.avatar_url):
                profile.change_avatar_url(command.avatar_url)

            await self._uow.profiles.save_profile_changes(profile)
