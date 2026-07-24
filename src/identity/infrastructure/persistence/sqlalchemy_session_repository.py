from datetime import datetime
from uuid import UUID

from sqlalchemy import RowMapping, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from src.identity.domain.entities import Session
from src.identity.infrastructure.persistence.tables import sessions_table
from src.shared.domain.exceptions import ConcurrentModificationError


class SqlAlchemySessionRepository:
    """Репозиторий пользовательских сессий на основе SQLAlchemy Core.

    Реализует полный набор операций CRUD для доменной сущности
    ``Session`` над таблицей ``sessions``.

    Parameters
    ----------
    connection : AsyncConnection
        Асинхронное подключение к базе данных SQLAlchemy.

    Notes
    -----
    Удовлетворяет протоколу ``SessionRepository`` структурно
    (duck typing) без явного наследования.
    """

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def add(self, session: Session) -> None:
        """Сохранить новую сессию в базу данных.

        Parameters
        ----------
        session : Session
            Доменная сущность сессии для сохранения.
        """
        await self._connection.execute(
            insert(sessions_table).values(
                id=session.id,
                identity_id=session.identity_id,
                session_secret=session.session_secret,
                expires_at=session.expires_at,
                last_used_at=session.last_used_at,
                revoked_at=session.revoked_at,
                ip_address=session.ip_address,
                user_agent=session.user_agent,
                version=session.version,
                created_at=session.created_at,
                updated_at=session.updated_at,
            )
        )

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
        result = await self._connection.execute(
            select(sessions_table).where(sessions_table.c.id == id)
        )

        if not (row := result.mappings().first()):
            return None

        return self._row_to_session(row)

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
        result = await self._connection.execute(
            select(sessions_table).where(
                sessions_table.c.session_secret == session_secret
            )
        )

        if not (row := result.mappings().first()):
            return None

        return self._row_to_session(row)

    async def mark_used(self, id: UUID, at: datetime) -> bool:
        """Зафиксировать факт использования сессии.

        Parameters
        ----------
        id : UUID
            Идентификатор сессии.
        at : datetime
            Момент использования.
        at : datetime | None, optional
            Временная метка использования пользовательской сессии.

        Returns
        -------
        bool
            ``True``, если время использования было обновлено,
            ``False``, если сессия с указанным идентификатором не найдена.
        """
        result = await self._connection.execute(
            update(sessions_table)
            .values(last_used_at=at)
            .where(sessions_table.c.id == id)
        )

        return result.rowcount == 1

    async def save_rotation(self, session: Session) -> None:
        """Сохранить ротированный секрет сессии и обновлённый срок действия.

        Обновляет секрет сессии и срок её действия в базе данных
        с проверкой версии агрегата.

        После успешного обновления вызывает ``session.upgrade()``
        для синхронизации версии объекта Python с базой данных.

        Parameters
        ----------
        session : Session
            Доменная сущность сессии с уже ротированным секретом
            и актуальной версией.

        Raises
        ------
        ConcurrentModificationError
            Если версия ``session`` не совпадает с версией
            в базе данных.
        """
        result = await self._connection.execute(
            update(sessions_table)
            .values(
                session_secret=session.session_secret,
                expires_at=session.expires_at,
                version=sessions_table.c.version + 1,
                updated_at=session.updated_at,
            )
            .where(
                sessions_table.c.id == session.id,
                sessions_table.c.version == session.version,
            )
        )

        if result.rowcount != 1:
            raise ConcurrentModificationError(session.id, "Session")

        session.upgrade()

    async def save_revocation(self, session: Session) -> None:
        """Сохранить отзыв сессии.

        Обновляет признак отзыва сессии (``revoked_at``) в базе данных
        с проверкой версии агрегата.

        После успешного обновления вызывает ``session.upgrade()``
        для синхронизации версии объекта Python с базой данных.

        Parameters
        ----------
        session : Session
            Доменная сущность сессии с уже установленным ``revoked_at``
            и актуальной версией.

        Raises
        ------
        ConcurrentModificationError
            Если версия ``session`` не совпадает с версией
            в базе данных.
        """
        result = await self._connection.execute(
            update(sessions_table)
            .values(
                revoked_at=session.revoked_at,
                version=sessions_table.c.version + 1,
                updated_at=session.updated_at,
            )
            .where(
                sessions_table.c.id == session.id,
                sessions_table.c.version == session.version,
            )
        )

        if result.rowcount != 1:
            raise ConcurrentModificationError(session.id, "Session")

        session.upgrade()

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
        result = await self._connection.execute(
            update(sessions_table)
            .values(revoked_at=datetime.now())
            .where(sessions_table.c.identity_id == identity_id)
        )

        return result.rowcount

    @staticmethod
    def _row_to_session(row: RowMapping) -> Session:
        """Преобразовать строку результата запроса в доменную сущность.

        Parameters
        ----------
        row : RowMapping
            Строка результата запроса (mapping).

        Returns
        -------
        Session
            Доменная сущность сессии.
        """
        return Session(
            id=row["id"],
            identity_id=row["identity_id"],
            session_secret=row["session_secret"],
            expires_at=row["expires_at"],
            last_used_at=row["last_used_at"],
            revoked_at=row["revoked_at"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            version=row["version"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
