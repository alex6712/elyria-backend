from datetime import UTC, datetime
from typing import Self
from uuid import UUID

from src.identity.domain.exceptions import SessionInvalidError
from src.shared.domain.entities import Auditable, Identifiable


class Session(Identifiable[UUID], Auditable):
    """Доменная сущность пользовательской сессии.

    Представляет собой одну аутентифицированную сессию пользователя
    в системе. Каждая сессия идентифицируется уникальным ключом
    и привязана к конкретному пользователю.

    Сессия содержит временные метки создания, последнего использования,
    истечения срока действия, отзыва сессии, последнего обновления,
    а также секрет сессии, используемый для продления сессии.

    Attributes
    ----------
    id : UUID
        Уникальный идентификатор сессии.
    identity_id : UUID
        Идентификатор учётной записи, которой принадлежит сессия.
    session_secret : str
        Уникальный секрет сессии, используемый для обновления сессии.
    expires_at : datetime
        Дата и время истечения срока действия сессии.
    last_used_at : datetime
        Дата и время последнего использования сессии.
    revoked_at : datetime | None
        Дата и время принудительного завершения сессии.
        ``None``, если сессия не была отозвана.
    ip_address : str | None
        IP-адрес, с которого была создана сессия.
    user_agent : str | None
        User-Agent клиента при создании сессии.
    created_at : datetime
        Дата и время создания сессии.
    updated_at : datetime | None
        Дата и время последнего изменения сессии.

    Notes
    -----
    Согласно решению, симметричному ADR-0004 (принятому для ``Profile``),
    методы ``extend`` и ``rotate_secret`` запрещены для отозванной
    или истёкшей сессии. При нарушении возбуждается
    ``SessionInvalidError``. Это решение оформлено отдельным ADR-0005.
    """

    def __init__(
        self,
        id: UUID,
        identity_id: UUID,
        session_secret: str,
        expires_at: datetime,
        last_used_at: datetime,
        revoked_at: datetime | None,
        ip_address: str | None,
        user_agent: str | None,
        created_at: datetime,
        updated_at: datetime | None,
    ) -> None:
        self.id = id
        self.identity_id = identity_id
        self.session_secret = session_secret
        self.expires_at = expires_at
        self.last_used_at = last_used_at
        self.revoked_at = revoked_at
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def issue(
        cls,
        id: UUID,
        identity_id: UUID,
        session_secret: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Self:
        """Создать новую сессию пользователя.

        Parameters
        ----------
        id : UUID
            Уникальный идентификатор сессии пользователя.
        identity_id : UUID
            Идентификатор учётной записи, которой принадлежит сессия.
        session_secret : str
            Уникальный секрет сессии, выпущенный Infrastructure Layer.
        expires_at : datetime
            Момент истечения срока действия сессии.
        ip_address : str | None, optional
            IP-адрес клиента на момент создания сессии.
        user_agent : str | None, optional
            User-Agent клиента на момент создания сессии.

        Returns
        -------
        Session
            Новая, не отозванная сессия.
        """
        return cls(
            id=id,
            identity_id=identity_id,
            session_secret=session_secret,
            expires_at=expires_at,
            last_used_at=(now := datetime.now(UTC)),
            revoked_at=None,
            ip_address=ip_address,
            user_agent=user_agent,
            updated_at=None,
            created_at=now,
        )

    def is_revoked(self) -> bool:
        """Проверить, отозвана ли сессия.

        Returns
        -------
        bool
            ``True``, если сессия была принудительно завершена.
        """
        return self.revoked_at is not None

    def is_expired(self, now: datetime | None = None) -> bool:
        """Проверить, истёк ли срок действия сессии.

        Parameters
        ----------
        now : datetime | None, optional
            Момент времени для сравнения. Если не передан,
            используется текущее время.

        Returns
        -------
        bool
            ``True``, если срок действия сессии истёк.
        """
        return (now or datetime.now(UTC)) >= self.expires_at

    def is_valid(self, now: datetime | None = None) -> bool:
        """Проверить, что сессия активна: не отозвана и не истекла.

        Parameters
        ----------
        now : datetime | None, optional
            Момент времени для проверки истечения срока действия.

        Returns
        -------
        bool
            ``True``, если сессия не отозвана и не истекла.
        """
        return not self.is_revoked() and not self.is_expired(now)

    def mark_used(self, at: datetime | None = None) -> None:
        """Зафиксировать факт использования сессии.

        Parameters
        ----------
        at : datetime | None, optional
            Момент использования. Если не передан, используется
            текущее время.

        Notes
        -----
        Не проверяет валидность сессии: предполагается, что
        Application Layer вызывает данный метод только после
        собственной проверки ``is_valid`` в рамках сценария
        аутентификации запроса.
        """
        self.last_used_at = (moment := (at or datetime.now(UTC)))
        self._touch(moment)

    def rotate_secret(self, new_session_secret: str, new_expires_at: datetime) -> None:
        """Заменить секрет сессии и продлить срок её действия.

        Parameters
        ----------
        new_session_secret : str
            Новый секрет сессии.
        new_expires_at : datetime
            Новый момент истечения срока действия сессии.

        Raises
        ------
        SessionInvalidError
            Если сессия отозвана или истёк срок её действия.

        Notes
        -----
        Используется в сценарии обновления сессии (refresh),
        когда старый секрет должен быть инвалидирован в пользу
        нового, а не создания новой сессии с нуля.
        """
        self._ensure_valid()
        self.session_secret = new_session_secret
        self.expires_at = new_expires_at
        self._touch()

    def revoke(self) -> None:
        """Принудительно завершить сессию.

        Notes
        -----
        Операция идемпотентна: повторный вызов для уже отозванной
        сессии не изменяет ``revoked_at`` и не обновляет ``updated_at``.
        Разрешена в любом состоянии сессии, включая уже истёкшую -
        отзыв не является операцией, требующей валидности сессии.
        """
        if self.is_revoked():
            return

        self.revoked_at = (moment := datetime.now(UTC))
        self._touch(moment)

    def _ensure_valid(self) -> None:
        """Проверить, что сессия не отозвана и не истекла.

        Raises
        ------
        SessionInvalidError
            Если сессия отозвана или истёк срок её действия.

        Notes
        -----
        Реализует инвариант, симметричный ADR-0004: операции
        ``extend`` и ``rotate_secret`` запрещены для невалидной
        сессии. Решение описано в ADR-0005.
        """
        if not self.is_valid():
            raise SessionInvalidError(self.id)

    def __repr__(self) -> str:
        return (
            "Session("
            f"id={self.id!r}, "
            f"identity_id={self.identity_id!r}, "
            f"expires_at={self.expires_at!r}, "
            f"last_used_at={self.last_used_at!r}, "
            f"revoked_at={self.revoked_at!r}, "
            f"ip_address={self.ip_address!r}, "
            f"user_agent={self.user_agent!r}, "
            f"created_at={self.created_at!r}, "
            f"updated_at={self.updated_at!r})"
        )
