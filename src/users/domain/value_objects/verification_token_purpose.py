from enum import StrEnum, auto


class VerificationTokenPurpose(StrEnum):
    """Назначение токена подтверждения.

    Определяет, для какой бизнес-операции выпущен токен
    подтверждения. Набор значений расширяется по мере появления
    новых операций, требующих подтверждения.

    See Also
    --------
    :attr:`~src.users.domain.entities.verification_token.VerificationToken.purpose`
        Назначение, хранимое вместе с токеном подтверждения.
    """

    EMAIL_VERIFICATION = auto()
    """Подтверждение адреса электронной почты пользователя."""
