from src.shared.application.exceptions import TokenRevokedError
from src.shared.application.ports.persistence import TokenBlacklist
from src.shared.application.ports.security import TokenVerifier
from src.users.application.dto.commands import ChangePasswordCommand
from src.users.application.exceptions import (
    CompromisedPasswordError,
    IdentityNotFoundError,
    IncorrectCurrentPasswordError,
    NewPasswordSameAsOldError,
)
from src.users.application.ports import UsersUnitOfWork
from src.users.application.ports.security import (
    CompromisedPasswordChecker,
    PasswordHasher,
)


class ChangePasswordCommandHandler:
    """Обработчик команды смены пароля пользователя.

    Проверяет подлинность access-токена и его отсутствие в чёрном
    списке, подтверждает операцию текущим паролем, проверяет новый
    пароль на совпадение со старым и на утечку данных, изменяет хэш
    пароля учётной записи и отзывает все прочие сессии пользователя.
    Сессия, в контексте которой выполнена смена пароля, остаётся
    активной.

    Parameters
    ----------
    uow : UsersUnitOfWork
        Единица работы, обеспечивающая атомарный доступ к репозиториям
        учётных записей и сессий.
    password_hasher : PasswordHasher
        Сервис хеширования паролей для проверки текущего пароля
        и хеширования нового.
    compromised_password_checker : CompromisedPasswordChecker
        Сервис проверки нового пароля на утечки данных.
    token_verifier : TokenVerifier
        Сервис проверки подлинности access-токенов и извлечения их
        утверждений.
    token_blacklist : TokenBlacklist
        Хранилище отозванных access-токенов.
    """

    def __init__(
        self,
        uow: UsersUnitOfWork,
        password_hasher: PasswordHasher,
        compromised_password_checker: CompromisedPasswordChecker,
        token_verifier: TokenVerifier,
        token_blacklist: TokenBlacklist,
    ) -> None:
        self._uow = uow
        self._password_hasher = password_hasher
        self._compromised_password_checker = compromised_password_checker
        self._token_verifier = token_verifier
        self._token_blacklist = token_blacklist

    async def execute(self, command: ChangePasswordCommand) -> None:
        """Изменить пароль пользователя.

        Подтверждает операцию текущим паролем, заменяет пароль новым
        и отзывает все сессии пользователя, кроме текущей. Все изменения
        сохраняются атомарно в рамках единицы работы.

        Parameters
        ----------
        command : ChangePasswordCommand
            Объект с данными для смены пароля, содержащий access-токен,
            текущий и новый пароли.

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
        IdentityNotFoundError
            Если учётная запись из токена не найдена.
        IncorrectCurrentPasswordError
            Если текущий пароль не совпадает с сохранённым хэшем.
        NewPasswordSameAsOldError
            Если новый пароль совпадает с текущим паролем.
        CompromisedPasswordError
            Если новый пароль встречается в известных утечках данных.
        ConcurrentModificationError
            Если версия учётной записи изменилась с момента загрузки.
        """
        claims = self._token_verifier.verify(command.access_token)

        if await self._token_blacklist.is_revoked(claims.token_id):
            raise TokenRevokedError("Passed access token has been revoked.")

        if await self._compromised_password_checker.is_compromised(
            command.new_password
        ):
            raise CompromisedPasswordError(
                "Password has been compromised and cannot be used."
            )

        async with self._uow:
            identity = await self._uow.identities.get_by_id(claims.user_id)

            if identity is None:
                raise IdentityNotFoundError(f"Identity {claims.user_id} not found.")

            current_hash = identity.password_hash

            if not self._password_hasher.verify(command.current_password, current_hash):
                raise IncorrectCurrentPasswordError("Current password is incorrect.")

            if self._password_hasher.verify(command.new_password, current_hash):
                raise NewPasswordSameAsOldError(
                    "New password must differ from current."
                )

            identity.change_password_hash(
                self._password_hasher.hash(command.new_password)
            )
            await self._uow.identities.save_password_hash(identity)

            _ = await self._uow.sessions.revoke_all_by_identity_id(
                claims.user_id, except_session_id=claims.session_id
            )
