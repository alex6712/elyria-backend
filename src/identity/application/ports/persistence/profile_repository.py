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
        ...

    async def change_display_name(
        self, identity_id: UUID, new_display_name: DisplayName
    ) -> bool:
        """Изменить отображаемое имя пользователя.

        Parameters
        ----------
        identity_id : UUID
            Идентификатор учётной записи пользователя.
        new_display_name : DisplayName
            Новое отображаемое имя.

        Returns
        -------
        bool
            ``True``, если отображаемое имя было изменено,
            ``False``, если пользователь с указанным идентификатором не найден.
        """
        ...
