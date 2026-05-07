from typing import Annotated
from uuid import UUID

from app.core.types import UNIQUE, UNSET, Maybe
from app.schemas.dto.base import (
    BaseCreateDTO,
    BaseFilterOneDTO,
    BaseSQLCoreDTO,
    BaseUpdateDTO,
)


class UserDTO(BaseSQLCoreDTO):
    """DTO для представления пользователя системы.

    Attributes
    ----------
    username : str
        Логин пользователя для входа в систему.
    avatar_url : str | None
        URL аватара пользователя.
    is_active : bool
        Статус пользователя (True - активный или False - заблокирован)
    """

    username: str
    avatar_url: str | None
    is_active: bool


class UserWithCredentialsDTO(UserDTO):
    """DTO для представления пользователя системы (с учётными данными).

    Наследуется от `UserDTO` вместе с остальными атрибутами пользователя.
    Является строго внутренним DTO, никогда не передаётся клиенту.

    Attributes
    ----------
    password_hash : str
        Хэш пароля пользователя.
    """

    password_hash: str


class CreatorDTO(UserDTO):
    """DTO для представления создателя сущности.

    Notes
    -----
    Наследуется от `UserDTO`, имеет тот же самый
    набор атрибутов. Выделен в отдельный класс из
    соображений семантики.
    """

    pass


class PartnerDTO(UserDTO):
    """DTO для представления партнёра пользователя.

    Notes
    -----
    Наследуется от `UserDTO`, имеет тот же самый
    набор атрибутов. Выделен в отдельный класс из
    соображений семантики.
    """

    pass


class FilterOneUserDTO(BaseFilterOneDTO):
    """DTO для поиска одной записи пользователя по идентификатору или имени пользователя.

    Требует передачи хотя бы одного из уникальных полей: `id` или `username`.
    Используется в сервисах, где пользователя можно найти как по его собственному
    идентификатору, так и по уникальному имени.

    Attributes
    ----------
    id : Maybe[UUID]
        Идентификатор пользователя. Является уникальным полем - достаточно передать
        только его для однозначного нахождения записи.
    username : Maybe[str]
        Имя пользователя. Является уникальным полем - достаточно передать только его
        для однозначного нахождения записи.
    """

    id: Annotated[Maybe[UUID], UNIQUE] = UNSET
    username: Annotated[Maybe[str], UNIQUE] = UNSET


class CreateUserDTO(BaseCreateDTO):
    """DTO для создания нового пользователя.

    Attributes
    ----------
    username : str
        Имя пользователя.
    password_hash : str
        Хэш пароля пользователя.
    """

    username: str
    password_hash: str


class UpdateUserDTO(BaseUpdateDTO):
    """DTO для частичного обновления пользователя.

    Attributes
    ----------
    first_name : Maybe[str]
        Новое реальное имя пользователя. Если `UNSET` - поле не изменяется.
        Временно не обрабатывается.
    avatar_url : Maybe[str]
        Новый URL аватара пользователя. Если `UNSET` - поле не изменяется.
    password_hash : Maybe[str]
        Новый хэшированный пароль пользователя. Если `UNSET` - поле не изменяется.
    """

    # first_name: Maybe[str] = UNSET
    avatar_url: Maybe[str] = UNSET
    password_hash: Maybe[str] = UNSET
