from typing import Protocol, runtime_checkable
from uuid import UUID

from src.application.shared.ports.persistence import BaseRepository
from src.domain.users.entities import User
from src.domain.users.value_objects import DisplayName, Username


@runtime_checkable
class UserRepository(BaseRepository[UUID, User], Protocol):
    """Порт репозитория пользователей.

    Определяет контракт для операций сохранения и получения
    пользователей. Расширяет базовый репозиторий методами,
    специфичными для домена пользователей: поиск по имени,
    смена пароля и отображаемого имени.

    Notes
    -----
    Реализация данного порта должна гарантировать уникальность
    имени пользователя.
    """

    async def add(self, user: User) -> None:
        """Сохранить нового пользователя.

        Parameters
        ----------
        user : User
            Доменная сущность пользователя для сохранения.

        Raises
        ------
        AlreadyExistsException
            Если пользователь с таким идентификатором или именем
            уже существует.
        """
        ...

    async def get_by_username(self, username: Username) -> User:
        """Получить пользователя по имени пользователя.

        Parameters
        ----------
        username : Username
            Имя пользователя для поиска.

        Returns
        -------
        User
            Найденный пользователь.

        Raises
        ------
        NotFoundException
            Если пользователь с указанным именем не найден.
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

    async def change_display_name(
        self, id: UUID, new_display_name: DisplayName
    ) -> bool:
        """Изменить отображаемое имя пользователя.

        Parameters
        ----------
        id : UUID
            Идентификатор пользователя.
        new_display_name : DisplayName
            Новое отображаемое имя.

        Returns
        -------
        bool
            ``True``, если отображаемое имя было изменено,
            ``False``, если пользователь с указанным идентификатором не найден.
        """
        ...
