from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TokenClaimsDTO(BaseModel):
    """Утверждения, содержащиеся в токене аутентификации.

    Представляет сведения, необходимые для идентификации пользователя,
    проверки типа токена и определения срока его действия.

    Данный объект используется Application Layer при взаимодействии с
    портами выпуска и проверки токенов. Он не содержит сведений о формате
    сериализации токена или используемом алгоритме подписи.

    Attributes
    ----------
    user_id : UUID
        Идентификатор пользователя, которому принадлежит токен.
    expires_at : datetime
        Момент истечения срока действия токена.
    issued_at : datetime
        Момент выпуска токена.
    token_id : UUID
        Идентификатор токена.
    session_id : UUID
        Идентификатор пользовательской сессии.
    """

    user_id: UUID
    expires_at: datetime
    issued_at: datetime
    token_id: UUID
    session_id: UUID

    model_config = ConfigDict(frozen=True)
