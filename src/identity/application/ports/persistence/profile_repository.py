from typing import Protocol, runtime_checkable
from uuid import UUID

from src.identity.domain.entities import Profile
from src.identity.domain.value_objects import DisplayName


@runtime_checkable
class ProfileRepository(Protocol):
    """Порт репозитория профилей пользователей.

    Определяет контракт для операций сохранения, получения
    и изменения отображаемого имени профилей пользователей.

    Notes
    -----
    Реализация данного порта должна гарантировать уникальность
    идентификатора пользователя.
    """

    async def add(self, profile: Profile) -> None:
        """Сохранить новый профиль пользователя.

        Parameters
        ----------
        profile : Profile
            Доменная сущность профиля для сохранения.
        """
        ...

    async def get_by_id(self, id: UUID) -> Profile:
        """Получить профиль пользователя по идентификатору.

        Parameters
        ----------
        id : UUID
            Идентификатор пользователя.

        Returns
        -------
        Profile
            Найденный профиль пользователя.
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
