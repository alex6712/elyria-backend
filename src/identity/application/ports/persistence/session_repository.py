from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from src.identity.domain.entities import Session


@runtime_checkable
class SessionRepository(Protocol):
    """Порт репозитория пользовательских сессий.

    Определяет контракт для операций сохранения, получения
    и изменения состояния сессий пользователей.

    Notes
    -----
    Реализация данного порта должна гарантировать уникальность
    секрета сессии.
    """

    async def add(self, session: Session) -> None:
        """Сохранить новую сессию.

        Parameters
        ----------
        session : Session
            Доменная сущность сессии для сохранения.
        """
        ...

    async def get_by_id(self, id: UUID) -> Session | None:
        """Получить сессию по идентификатору.

        Parameters
        ----------
        id : UUID
            Идентификатор сессии.

        Returns
        -------
        Session | None
            Найденная сессия либо ``None``, если сессия
            с указанным идентификатором не существует.
        """
        ...

    async def get_by_session_secret(self, session_secret: str) -> Session | None:
        """Получить сессию по секрету сессии.

        Parameters
        ----------
        session_secret : str
            Секрет сессии.

        Returns
        -------
        Session | None
            Найденная сессия либо ``None``, если сессия
            с указанным секретом не существует.
        """
        ...

    async def mark_used(self, id: UUID, at: datetime) -> bool:
        """Зафиксировать факт использования сессии.

        Parameters
        ----------
        id : UUID
            Идентификатор сессии.
        at : datetime
            Момент использования.

        Returns
        -------
        bool
            ``True``, если время использования было обновлено,
            ``False``, если сессия с указанным идентификатором не найдена.
        """
        ...

    async def rotate_secret(
        self,
        id: UUID,
        session_secret: str,
        new_session_secret: str,
        new_expires_at: datetime,
    ) -> bool:
        """Заменить секрет сессии и продлить срок её действия.

        Parameters
        ----------
        id : UUID
            Идентификатор сессии.
        session_secret : str
            Текущий секрет сессии.
        new_session_secret : str
            Новый секрет сессии.
        new_expires_at : datetime
            Новый момент истечения срока действия сессии.

        Returns
        -------
        bool
            ``True``, если секрет был изменён,
            ``False``, если сессия с указанными идентификатором и секретом не найдена.

        Notes
        -----
        Реализация обязана проверить соответствие секрета сессии и идентификатора
        сессии внутри одной операции перед установкой нового секрета сессии.
        """
        ...

    async def revoke(self, id: UUID) -> bool:
        """Принудительно завершить сессию.

        Parameters
        ----------
        id : UUID
            Идентификатор сессии.

        Returns
        -------
        bool
            ``True``, если сессия была отозвана,
            ``False``, если сессия с указанным идентификатором не найдена.
        """
        ...

    async def revoke_all_by_identity_id(self, identity_id: UUID) -> int:
        """Принудительно завершить все сессии учётной записи.

        Parameters
        ----------
        identity_id : UUID
            Идентификатор учётной записи.

        Returns
        -------
        int
            Количество отозванных сессий.
        """
        ...
