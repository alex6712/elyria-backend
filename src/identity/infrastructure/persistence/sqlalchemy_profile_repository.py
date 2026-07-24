from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from src.identity.domain.entities import Profile
from src.identity.domain.value_objects import DisplayName
from src.identity.infrastructure.persistence.tables import profiles_table
from src.shared.domain.exceptions import ConcurrentModificationError


class SqlAlchemyProfileRepository:
    """Репозиторий профилей пользователей на основе SQLAlchemy Core.

    Реализует полный набор операций CRUD для доменной сущности
    ``Profile`` над таблицей ``profiles``.

    Parameters
    ----------
    connection : AsyncConnection
        Асинхронное подключение к базе данных SQLAlchemy.

    Notes
    -----
    Удовлетворяет протоколу ``ProfileRepository`` структурно
    (duck typing) без явного наследования.
    """

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def add(self, profile: Profile) -> None:
        """Сохранить новый профиль пользователя в базу данных.

        Parameters
        ----------
        profile : Profile
            Доменная сущность профиля для сохранения.
        """
        await self._connection.execute(
            insert(profiles_table).values(
                id=profile.id,
                identity_id=profile.identity_id,
                display_name=profile.display_name.value,
                avatar_url=profile.avatar_url,
                version=profile.version,
                created_at=profile.created_at,
                updated_at=profile.updated_at,
            )
        )

    async def get_by_identity_id(self, identity_id: UUID) -> Profile | None:
        """Получить профиль пользователя по идентификатору учётной записи.

        Parameters
        ----------
        identity_id : UUID
            Идентификатор учётной записи пользователя.

        Returns
        -------
        Profile | None
            Найденный профиль пользователя либо ``None``, если профиль
            с указанным идентификатором учётной записи не существует.
        """
        result = await self._connection.execute(
            select(profiles_table).where(profiles_table.c.identity_id == identity_id)
        )

        if not (row := result.mappings().first()):
            return None

        return Profile(
            id=row["id"],
            identity_id=row["identity_id"],
            display_name=DisplayName(row["display_name"]),
            avatar_url=row["avatar_url"],
            version=row["version"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def save_display_name(self, profile: Profile) -> None:
        """Сохранить изменённое отображаемое имя профиля.

        Обновляет отображаемое имя в базе данных с проверкой
        версии агрегата.

        После успешного обновления вызывает ``profile.upgrade()``
        для синхронизации версии объекта Python с базой данных.

        Parameters
        ----------
        profile : Profile
            Доменная сущность профиля с изменённым отображаемым
            именем и актуальной версией.

        Raises
        ------
        ConcurrentModificationError
            Если версия ``profile`` не совпадает с версией
            в базе данных.
        """
        result = await self._connection.execute(
            update(profiles_table)
            .values(
                display_name=profile.display_name.value,
                version=profiles_table.c.version + 1,
                updated_at=profile.updated_at,
            )
            .where(
                profiles_table.c.id == profile.id,
                profiles_table.c.version == profile.version,
            )
        )

        if result.rowcount != 1:
            raise ConcurrentModificationError(profile.id, "Profile")

        profile.upgrade()
