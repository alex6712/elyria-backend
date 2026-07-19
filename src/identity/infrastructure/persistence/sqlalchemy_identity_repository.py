from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from src.identity.domain.entities import Identity
from src.identity.domain.exceptions import UsernameAlreadyExistsException
from src.identity.domain.value_objects import Username
from src.shared.infrastructure.persistence.sqlalchemy.tables import users_table


class SQLAlchemyIdentityRepository:
    """Репозиторий учётных записей на основе SQLAlchemy Core.

    Реализует полный набор операций CRUD для доменной сущности
    ``Identity`` над таблицей ``users``. Обрабатывает нарушение
    уникальности имени пользователя и транслирует его в доменное
    исключение ``UsernameAlreadyExistsException``.

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
        UsernameAlreadyExistsException
            Если пользователь с таким ``username`` уже существует
            в базе данных.
        """
        try:
            await self._connection.execute(
                insert(users_table).values(
                    id=identity.id,
                    username=identity.username,
                    password_hash=identity.password_hash,
                    is_active=identity.is_active,
                    created_at=identity.created_at,
                    updated_at=identity.updated_at,
                )
            )
        except IntegrityError as e:
            if "uq_users_username" in str(e):
                raise UsernameAlreadyExistsException(
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
            select(
                users_table,
                users_table.c.id,
                users_table.c.username,
                users_table.c.password_hash,
                users_table.c.is_active,
                users_table.c.created_at,
                users_table.c.updated_at,
            ).where(users_table.c.id == id)
        )

        if not (row := result.mappings().first()):
            return None

        return Identity(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            is_active=row["is_active"],
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
            select(
                users_table,
                users_table.c.id,
                users_table.c.username,
                users_table.c.password_hash,
                users_table.c.is_active,
                users_table.c.created_at,
                users_table.c.updated_at,
            ).where(users_table.c.username == username)
        )

        if not (row := result.mappings().first()):
            return None

        return Identity(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def change_password_hash(self, id: UUID, new_password_hash: str) -> bool:
        """Изменить хэш пароля пользователя.

        Parameters
        ----------
        id : UUID
            Идентификатор пользователя.
        new_password_hash : str
            Новый хэш пароля.

        Returns
        -------
        bool
            ``True``, если хэш пароля был изменён,
            ``False``, если пользователь с указанным идентификатором не найден.
        """
        result = await self._connection.execute(
            update(users_table)
            .values(password_hash=new_password_hash)
            .where(users_table.c.id == id)
        )

        return result.rowcount == 1
