from typing import Protocol, runtime_checkable
from uuid import UUID

from src.identity.domain.entities import Identity
from src.identity.domain.value_objects import Username


@runtime_checkable
class IdentityRepository(Protocol):
    """Порт репозитория учётных записей (identity).

    Определяет контракт для операций сохранения и получения
    учётных записей системы.

    Notes
    -----
    Реализация данного порта должна гарантировать уникальность
    имени пользователя.
    """

    async def add(self, identity: Identity) -> None:
        """Сохранить новую учётную запись.

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
        ...

    async def get_by_id(self, id: UUID) -> Identity | None:
        """Получить учётную запись по идентификатору.

        Parameters
        ----------
        id : UUID
            Идентификатор учётной записи.

        Returns
        -------
        Identity | None
            Найденная учётная запись или None.
        """
        ...

    async def get_by_username(self, username: Username) -> Identity | None:
        """Получить учётную запись по имени пользователя.

        Parameters
        ----------
        username : Username
            Имя пользователя для поиска.

        Returns
        -------
        Identity | None
            Найденная учётная запись или None.
        """
        ...

    async def save_password_hash(self, identity: Identity) -> None:
        """Сохранить изменённый хэш пароля учётной записи.

        Выполняет атомарное обновление хэша пароля с проверкой
        версии агрегата. Перед вызовом этого метода необходимо изменить
        хэш пароля через метод доменной сущности.

        После успешного обновления репозиторий увеличивает версию
        переданной сущности через ``identity.upgrade()``.

        Parameters
        ----------
        identity : Identity
            Доменная сущность учётной записи с уже изменённым
            хэшем пароля и актуальной версией.

        Raises
        ------
        ConcurrentModificationError
            Если версия ``identity`` не совпадает с версией
            в хранилище.
        """
        ...
