from typing import Protocol, runtime_checkable
from uuid import UUID

from src.users.domain.entities import Session


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

    async def save_refresh(self, session: Session) -> None:
        """Сохранить результат обновления (продления) сессии.

        Выполняет атомарную запись нового секрета, обновлённого срока действия
        и метки последнего использования с проверкой версии агрегата.

        После успешного обновления репозиторий увеличивает версию переданной
        сущности через ``session.upgrade()`` для предотвращения состояния гонки.

        Parameters
        ----------
        session : Session
            Доменная сущность сессии с обновлёнными полями (``secret``,
            ``expires_at``, ``last_used_at``) и актуальной версией.

        Raises
        ------
        ConcurrentModificationError
            Если версия ``session`` не совпадает с версией в хранилище.
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

    async def revoke_all_by_identity_id(
        self, identity_id: UUID, *, except_session_id: UUID | None = None
    ) -> int:
        """Принудительно завершить все сессии учётной записи.

        Массовая операция, выполняющая отзыв всех активных сессий
        пользователя одной командой UPDATE без проверки версии каждой
        сессии. Сессии, отозванные ранее, повторно не отзываются:
        их ``revoked_at`` и ``updated_at`` остаются неизменными.

        Parameters
        ----------
        identity_id : UUID
            Идентификатор учётной записи.
        except_session_id : UUID | None, optional
            Идентификатор сессии, которую отзыв не затрагивает
            (например, сессия, в контексте которой выполняется
            смена пароля). ``None`` означает отзыв всех сессий
            учётной записи без исключений.

        Returns
        -------
        int
            Количество отозванных сессий.
        """
        ...
