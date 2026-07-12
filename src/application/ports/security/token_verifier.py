from typing import Protocol, runtime_checkable

from src.application.dto.security.token_claims import TokenClaimsDTO


@runtime_checkable
class TokenVerifier(Protocol):
    """Порт проверки токенов.

    Определяет контракт компонента, отвечающего за проверку подлинности
    токена и извлечение содержащихся в нём утверждений.

    Notes
    -----
    Реализация самостоятельно выполняет все необходимые проверки
    корректности токена, включая проверку подписи и срока действия.
    """

    def verify(self, token: str) -> TokenClaimsDTO:
        """Проверить токен и извлечь содержащиеся в нём утверждения.

        Parameters
        ----------
        token : str
            Подписанный токен.

        Returns
        -------
        TokenClaimsDTO
            Проверенные утверждения, содержащиеся в токене.

        Raises
        ------
        TokenExpiredException
            Если срок действия токена истёк.
        TokenSignatureInvalidException
            Если подпись токена не прошла проверку.
        TokenInvalidException
            Если в токене отсутствуют обязательные утверждения
            либо токен имеет некорректный формат.
        """
        ...
