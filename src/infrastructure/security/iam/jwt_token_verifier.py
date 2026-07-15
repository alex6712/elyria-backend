import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import ValidationError

from src.application.iam.dto import TokenClaimsDTO
from src.domain.iam.exceptions import (
    TokenExpiredException,
    TokenInvalidException,
    TokenSignatureInvalidException,
)


class JwtTokenVerifier:
    """Реализация порта ``TokenVerifier`` на основе JWT.

    Выполняет проверку подписи и срока действия JWT-токенов
    с использованием алгоритма асимметричной подписи Ed25519 (EdDSA).

    Извлекает утверждения из валидного токена и возвращает их
    в виде ``TokenClaimsDTO``.

    Parameters
    ----------
    issuer : str
        Издатель токена (значение утверждения ``iss``).
    public_key : Ed25519PublicKey
        Публичный ключ Ed25519 для проверки подписи токенов.
    algorithm : str
        Алгоритм подписи JWT (например, ``"EdDSA"``).
    """

    def __init__(
        self, issuer: str, public_key: Ed25519PublicKey, algorithm: str
    ) -> None:
        self._issuer = issuer
        self._public_key = public_key
        self._algorithm = algorithm

    def verify(self, token: str) -> TokenClaimsDTO:
        """Проверить подписанный JWT-токен и извлечь утверждения.

        Выполняет проверку подписи токена с использованием публичного
        ключа Ed25519, проверяет срок действия и наличие всех
        обязательных утверждений.

        Parameters
        ----------
        token : str
            Подписанный JWT-токен в компактном сериализованном
            формате.

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
        try:
            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=[self._algorithm],
                issuer=self._issuer,
                options={"require": ["iss", "sub", "exp", "iat", "jti", "sid"]},
            )
        except jwt.ExpiredSignatureError:
            raise TokenExpiredException("Signature of passed token has expired.")
        except jwt.InvalidSignatureError:
            raise TokenSignatureInvalidException(
                "Signature of passed token is invalid or damaged."
            )
        except jwt.InvalidTokenError as e:
            raise TokenInvalidException(str(e))

        try:
            return TokenClaimsDTO.model_validate(
                {
                    "user_id": payload["sub"],
                    "expires_at": payload["exp"],
                    "issued_at": payload["iat"],
                    "token_id": payload["jti"],
                    "session_id": payload["sid"],
                }
            )
        except ValidationError as e:
            raise TokenInvalidException(str(e)) from e
