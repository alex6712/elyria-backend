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

    async def save_rotation(self, session: Session) -> None:
        """Сохранить ротированный секрет сессии и обновлённый срок действия.

        Выполняет атомарное обновление секрета сессии и срока её действия
        с проверкой версии агрегата. Перед вызовом этого метода необходимо
        выполнить ротацию секрета через метод доменной сущности.

        После успешного обновления репозиторий увеличивает версию
        переданной сущности через ``session.upgrade()``.

        Parameters
        ----------
        session : Session
            Доменная сущность сессии с уже ротированным секретом
            и актуальной версией.

        Raises
        ------
        ConcurrentModificationError
            Если версия ``session`` не совпадает с версией
            в хранилище.
        """
        ...

    async def save_revocation(self, session: Session) -> None:
        """Сохранить отзыв сессии.

        Выполняет атомарное обновление признака отзыва сессии
        (``revoked_at``) с проверкой версии агрегата. Перед вызовом
        этого метода необходимо отозвать сессию через метод
        доменной сущности.

        После успешного обновления репозиторий увеличивает версию
        переданной сущности через ``session.upgrade()``.

        Parameters
        ----------
        session : Session
            Доменная сущность сессии с уже установленным ``revoked_at``
            и актуальной версией.

        Raises
        ------
        ConcurrentModificationError
            Если версия ``session`` не совпадает с версией
            в хранилище.
        """
        ...

    async def revoke_all_by_identity_id(self, identity_id: UUID) -> int:
        """Принудительно завершить все сессии учётной записи.

        Массовая операция, выполняющая отзыв всех сессий пользователя
        одной командой UPDATE без проверки версии каждой серии
        (неприменима для массовых операций).

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
