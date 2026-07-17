from datetime import datetime, timezone
from typing import Self
from uuid import UUID, uuid4

from src.domain.iam.exceptions import SessionInvalidException
from src.domain.shared.entities import Auditable, Identifiable


class Session(Identifiable[UUID], Auditable):
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
    revoked_at : datetime | None
        Дата и время принудительного завершения сессии.
        ``None``, если сессия не была отозвана.
    ip_address : str
        IP-адрес, с которого была создана сессия.
    user_agent : str
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
    ``SessionInvalidException``. Это решение оформлено отдельным ADR-0005.
    """

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        session_secret: str,
        expires_at: datetime,
        last_used_at: datetime,
        revoked_at: datetime | None,
        ip_address: str,
        user_agent: str,
        created_at: datetime,
        updated_at: datetime | None,
    ) -> None:
        self.id = id
        self.user_id = user_id
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
        user_id: UUID,
        session_secret: str,
        expires_at: datetime,
        ip_address: str,
        user_agent: str,
    ) -> Self:
        """Создать новую сессию пользователя.

        Parameters
        ----------
        user_id : UUID
            Идентификатор пользователя, которому принадлежит сессия.
        session_secret : str
            Уникальный секрет сессии, выпущенный Infrastructure Layer.
        expires_at : datetime
            Момент истечения срока действия сессии.
        ip_address : str
            IP-адрес клиента на момент создания сессии.
        user_agent : str
            User-Agent клиента на момент создания сессии.

        Returns
        -------
        Session
            Новая, не отозванная сессия.
        """
        return cls(
            id=uuid4(),
            user_id=user_id,
            session_secret=session_secret,
            expires_at=expires_at,
            last_used_at=(now := datetime.now(timezone.utc)),
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
        return (now or datetime.now(timezone.utc)) >= self.expires_at

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
        self.last_used_at = (moment := (at or datetime.now(timezone.utc)))
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
        SessionInvalidException
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

        self.revoked_at = (moment := datetime.now(timezone.utc))
        self._touch(moment)

    def _ensure_valid(self) -> None:
        """Проверить, что сессия не отозвана и не истекла.

        Raises
        ------
        SessionInvalidException
            Если сессия отозвана или истёк срок её действия.

        Notes
        -----
        Реализует инвариант, симметричный ADR-0004: операции
        ``extend`` и ``rotate_secret`` запрещены для невалидной
        сессии. Решение описано в ADR-0005.
        """
        if not self.is_valid():
            raise SessionInvalidException(self.id)

    def __eq__(self, other: object) -> bool:
        """Сравнить сессии по идентификатору.

        Parameters
        ----------
        other : object
            Объект для сравнения.

        Returns
        -------
        bool
            ``True``, если ``other`` является ``Session`` с тем же
            ``id``, иначе ``False`` или ``NotImplemented``.
        """
        if not isinstance(other, Session):
            return NotImplemented

        return self.id == other.id

    def __repr__(self) -> str:
        """Построить отладочное строковое представление сессии.

        Returns
        -------
        str
            Строка вида ``Session(id=..., user_id=..., revoked_at=...)``.
        """
        return (
            f"Session(id={self.id!r}, user_id={self.user_id!r}, "
            f"revoked_at={self.revoked_at!r})"
        )
