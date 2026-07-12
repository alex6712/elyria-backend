from datetime import datetime
from uuid import UUID


class Session:
    """Доменная сущность пользовательской сессии.

    Представляет собой одну аутентифицированную сессию пользователя
    в системе. Каждая сессия идентифицируется уникальным ключом
    и привязана к конкретному пользователю.

    Сессия содержит временные метки создания, последнего использования,
    истечения срока действия, отзыва сессии, последнего обновления,
    а также секрет сессии, используемый для продления сессии.

    Parameters
    ----------
    id : UUID
        Уникальный идентификатор сессии.
    user_id : UUID
        Идентификатор пользователя, которому принадлежит сессия.
    session_secret : str
        Уникальный секрет сессии, используемый для обновления сессии.
    expires_at : datetime
        Дата и время истечения срока действия сессии.
    last_used_at : datetime
        Дата и время последнего использования сессии.
    revoked_at : datetime
        Дата и время принудительного завершения сессии.
    ip_address : str
        IP-адрес, с которого была создана сессия.
    user_agent : str
        User-Agent клиента при создании сессии.
    updated_at : datetime
        Дата и время последнего изменения сессии.
    created_at : datetime
        Дата и время создания сессии.
    """

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        session_secret: str,
        expires_at: datetime,
        last_used_at: datetime,
        revoked_at: datetime,
        ip_address: str,
        user_agent: str,
        updated_at: datetime,
        created_at: datetime,
    ) -> None:
        self.id = id
        self.user_id = user_id
        self.session_secret = session_secret
        self.expires_at = expires_at
        self.last_used_at = last_used_at
        self.revoked_at = revoked_at
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.updated_at = updated_at
        self.created_at = created_at
