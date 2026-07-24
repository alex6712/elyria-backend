from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from src.identity.domain.entities import Identity
from src.identity.domain.exceptions import UsernameAlreadyExistsError
from src.identity.domain.value_objects import Username
from src.identity.infrastructure.persistence.tables import identities_table
from src.shared.domain.exceptions import ConcurrentModificationError


class SqlAlchemyIdentityRepository:
    """Репозиторий учётных записей на основе SQLAlchemy Core.

    Реализует полный набор операций CRUD для доменной сущности
    ``Identity`` над таблицей ``users``. Обрабатывает нарушение
    уникальности имени пользователя и транслирует его в доменное
    исключение ``UsernameAlreadyExistsError``.

    Parameters
    ----------
    connection : AsyncConnection
        Асинхронное подключение к базе данных SQLAlchemy.

    Notes
    -----
    Удовлетворяет протоколу ``IdentityRepository`` структурно
    (duck typing) без явного наследования.
    """

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def add(self, identity: Identity) -> None:
        """Сохранить новую учётную запись в базу данных.

        Выполняет вставку записи в таблицу ``users``. При нарушении
        ограничения уникальности имени пользователя преобразует
        ``IntegrityError`` в доменное исключение.

        Parameters
        ----------
        identity : Identity
            Доменная сущность учётной записи для сохранения.

        Raises
        ------
        UsernameAlreadyExistsError
            Если пользователь с таким ``username`` уже существует
            в базе данных.
        """
        try:
            await self._connection.execute(
                insert(identities_table).values(
                    id=identity.id,
                    username=identity.username,
                    password_hash=identity.password_hash,
                    is_active=identity.is_active,
                    version=identity.version,
                    created_at=identity.created_at,
                    updated_at=identity.updated_at,
                )
            )
        except IntegrityError as e:
            if "uq_users_username" in str(e):
                raise UsernameAlreadyExistsError(
                    f"User with username={identity.username} already exists."
                ) from e

            raise

    async def get_by_id(self, id: UUID) -> Identity | None:
        """Получить учётную запись по идентификатору.

        Parameters
        ----------
        id : UUID
            Идентификатор учётной записи.

        Returns
        -------
        Identity | None
            Найденная учётная запись либо ``None``, если запись
            с указанным идентификатором не существует.
        """
        result = await self._connection.execute(
            select(identities_table).where(identities_table.c.id == id)
        )

        if not (row := result.mappings().first()):
            return None

        return Identity(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            is_active=row["is_active"],
            version=row["version"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def get_by_username(self, username: Username) -> Identity | None:
        """Получить учётную запись по имени пользователя.

        Parameters
        ----------
        username : Username
            Имя пользователя для поиска.

        Returns
        -------
        Identity | None
            Найденная учётная запись либо ``None``, если запись
            с указанным именем пользователя не существует.
        """
        result = await self._connection.execute(
            select(identities_table, identities_table.c.id).where(
                identities_table.c.username == username
            )
        )

        if not (row := result.mappings().first()):
            return None

        return Identity(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            is_active=row["is_active"],
            version=row["version"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def save_password_hash(self, identity: Identity) -> None:
        """Сохранить изменённый хэш пароля учётной записи.

        Обновляет хэш пароля в базе данных с проверкой версии
        агрегата.

        После успешного обновления вызывает ``identity.upgrade()``
        для синхронизации версии объекта Python с базой данных.

        Parameters
        ----------
        identity : Identity
            Доменная сущность учётной записи с изменённым хэшем
            пароля и актуальной версией.

        Raises
        ------
        ConcurrentModificationError
            Если версия ``identity`` не совпадает с версией
            в базе данных.
        """
        result = await self._connection.execute(
            update(identities_table)
            .values(
                password_hash=identity.password_hash,
                version=identities_table.c.version + 1,
                updated_at=identity.updated_at,
            )
            .where(
                identities_table.c.id == identity.id,
                identities_table.c.version == identity.version,
            )
        )

        if result.rowcount != 1:
            raise ConcurrentModificationError(identity.id, "Identity")

        identity.upgrade()
