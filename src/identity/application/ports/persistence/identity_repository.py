from typing import Protocol, runtime_checkable
from uuid import UUID

from src.identity.domain.entities import Identity
from src.identity.domain.value_objects import Username


@runtime_checkable
class IdentityRepository(Protocol):
    """Порт репозитория учётных записей (identity).

    Определяет контракт для операций сохранения и получения
    учётных записей системы.
    """

    async def add(self, identity: Identity) -> None:
        """Сохранить новую учётную запись.

        Parameters
        ----------
        identity : Identity
            Доменная сущность учётной записи для сохранения.
        """
        ...

    async def get_by_id(self, id: UUID) -> Identity:
        """Получить учётную запись по идентификатору.

        Parameters
        ----------
        id : UUID
            Идентификатор учётной записи.

        Returns
        -------
        Identity
            Найденная учётная запись.
        """
        ...

    async def get_by_username(self, username: Username) -> Identity:
        """Получить учётную запись по имени пользователя.

        Parameters
        ----------
        username : Username
            Имя пользователя для поиска.

        Returns
        -------
        Identity
            Найденная учётная запись.
        """
        ...

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
        ...
