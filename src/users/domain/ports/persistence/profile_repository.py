from typing import Protocol, runtime_checkable
from uuid import UUID

from src.users.domain.entities import Profile


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

    async def get_by_id(self, profile_id: UUID) -> Profile | None:
        """Получить профиль пользователя по идентификатору профиля.

        Parameters
        ----------
        profile_id : UUID
            Уникальный идентификатор профиля.

        Returns
        -------
        Profile | None
            Найденный профиль пользователя либо ``None``, если профиль
            с указанным идентификатором не существует.
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

    async def save_profile_changes(self, profile: Profile) -> None:
        """Сохранить изменения профиля пользователя.

        Выполняет атомарное обновление сущности с проверкой версии
        агрегата. Метод используется для сохранения любых изменений.

        Перед вызовом необходимо изменить состояние доменной сущности.
        После успешного обновления репозиторий увеличивает версию через
        ``profile.upgrade()``.

        Parameters
        ----------
        profile : Profile
            Доменная сущность профиля с актуальными изменениями
            и версией.

        Raises
        ------
        ConcurrentModificationError
            Если версия ``profile`` не совпадает с версией
            в хранилище.
        """
        ...
