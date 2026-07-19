from datetime import datetime, timezone
from typing import Self
from uuid import UUID, uuid4

from src.identity.domain.exceptions import InactiveUserException
from src.identity.domain.value_objects import Username
from src.shared.domain.entities import Auditable, Identifiable


class Identity(Identifiable[UUID], Auditable):
    """Доменная сущность учётной записи пользователя.

    Представляет собой учётную запись (identity) пользователя
    в системе. Содержит идентификатор и метки аудита,
    наследуя функциональность от ``Identifiable`` и ``Auditable``.
    """

    def __init__(
        self,
        id: UUID,
        username: Username,
        password_hash: str,
        is_active: bool,
        created_at: datetime,
        updated_at: datetime | None,
    ) -> None:
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def register(cls, username: Username, password_hash: str) -> Self:
        return cls(
            id=uuid4(),
            username=username,
            password_hash=password_hash,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )

    def change_password(self, new_password_hash: str) -> None:
        """Изменить хэш пароля пользователя.

        Parameters
        ----------
        new_password_hash : str
            Новый хэш пароля, полученный из Infrastructure Layer.

        Raises
        ------
        InactiveUserException
            Если пользователь деактивирован.
        """
        self._ensure_active()
        self.password_hash = new_password_hash
        self._touch()

    def deactivate(self) -> None:
        """Деактивировать учётную запись пользователя.

        Notes
        -----
        Операция идемпотентна: повторный вызов для уже неактивного
        пользователя не изменяет состояние и не обновляет
        ``updated_at``.
        """
        if not self.is_active:
            return

        self.is_active = False
        self._touch()

    def activate(self) -> None:
        """Активировать учётную запись пользователя.

        Notes
        -----
        Единственный метод изменения состояния, доступный для
        неактивного пользователя (см. ADR-0004). Операция
        идемпотентна: повторный вызов для уже активного пользователя
        не изменяет состояние и не обновляет ``updated_at``.
        """
        if self.is_active:
            return

        self.is_active = True
        self._touch()

    def _ensure_active(self) -> None:
        """Проверить, что пользователь активен.

        Raises
        ------
        InactiveUserException
            Если ``is_active`` равен ``False``.

        Notes
        -----
        Реализует инвариант из ADR-0004: все методы изменения
        состояния, кроме ``activate``, запрещены для неактивного
        пользователя.
        """
        if not self.is_active:
            raise InactiveUserException(self.id)
