import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)

from src.application.dto.security.token_claims import TokenClaimsDTO


class JwtTokenIssuer:
    """Реализация порта ``TokenIssuer`` на основе JWT.

    Выпускает подписанные JWT-токены с использованием алгоритма
    асимметричной подписи Ed25519 (EdDSA).

    Формирует стандартные JWT-утверждения на основе переданного DTO
    ``TokenClaimsDTO`` и подписывает их переданным приватным ключом.

    Parameters
    ----------
    private_key : Ed25519PrivateKey
        Приватный ключ Ed25519 для подписи токенов.
    algorithm : str
        Алгоритм подписи JWT (например, ``"EdDSA"``).
    """

    def __init__(
        self, issuer: str, private_key: Ed25519PrivateKey, algorithm: str
    ) -> None:
        self._issuer = issuer
        self._private_key_bytes = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption(),
        )
        self._algorithm = algorithm

    def issue(self, claims: TokenClaimsDTO) -> str:
        """Выпустить подписанный JWT-токен.

        Преобразует ``TokenClaimsDTO`` в набор стандартных и
        пользовательских JWT-утверждений, после чего подписывает
        их с использованием алгоритма, указанного при инициализации.

        Parameters
        ----------
        claims : TokenClaimsDTO
            Утверждения для включения в токен.

        Returns
        -------
        str
            Подписанный JWT-токен в компактном сериализованном
            формате (три части, разделённые точками).
        """
        return jwt.encode(
            self._build_payload(claims),
            self._private_key_bytes,
            algorithm=self._algorithm,
        )

    def _build_payload(self, claims: TokenClaimsDTO) -> dict[str, str | int]:
        """Формирует словарь JWT-утверждений из DTO.

        Parameters
        ----------
        claims : TokenClaimsDTO
            Исходные утверждения.

        Returns
        -------
        dict[str, str | int]
            Словарь утверждений для передачи в ``jwt.encode``.
        """
        return {
            "iss": self._issuer,
            "sub": str(claims.user_id),
            "exp": int(claims.expires_at.timestamp()),
            "iat": int(claims.issued_at.timestamp()),
            "jti": str(claims.token_id),
            "sid": str(claims.session_id),
        }
