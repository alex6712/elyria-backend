from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from src.users.domain.entities import VerificationToken
from src.users.domain.value_objects import VerificationTokenPurpose


@runtime_checkable
class VerificationTokenRepository(Protocol):
    """Порт репозитория токенов подтверждения.

    Определяет контракт для сохранения, получения и аннулирования
    одноразовых токенов, подтверждающих выполнение операций,
    требующих проверки их инициатора.

    Notes
    -----
    Реализация данного порта обязана гарантировать уникальность
    значения ``token_hash``. Метод
    ``invalidate_active_by_identity_id`` не возбуждает исключений
    при нулевом числе обновлённых строк: отсутствие пригодных
    токенов для аннулирования является допустимым состоянием.
    """

    async def add(self, token: VerificationToken) -> None:
        """Сохранить новый токен подтверждения.

        Parameters
        ----------
        token : VerificationToken
            Доменная сущность токена для сохранения.

        Notes
        -----
        Реализация обязана гарантировать уникальность значения
        ``token_hash``.
        """
        ...

    async def get_by_token_hash(self, token_hash: str) -> VerificationToken | None:
        """Получить токен подтверждения по хешу токена.

        Parameters
        ----------
        token_hash : str
            Криптографический хеш токена.

        Returns
        -------
        VerificationToken | None
            Найденный токен либо ``None``, если токен с указанным
            хешем не существует.
        """
        ...

    async def invalidate_active_by_identity_id(
        self,
        identity_id: UUID,
        purpose: VerificationTokenPurpose,
        *,
        at: datetime,
    ) -> None:
        """Аннулировать пригодные токены учётной записи.

        Переводит в непригодное состояние все токены указанной
        учётной записи с заданным назначением, которые ещё не были
        применены или аннулированы.

        Parameters
        ----------
        identity_id : UUID
            Идентификатор учётной записи.
        purpose : VerificationTokenPurpose
            Назначение аннулируемых токенов.
        at : datetime
            Временная метка аннулирования. Записывается как в поле
            ``used_at``, так и в поле ``updated_at``.

        Notes
        -----
        Реализация не возбуждает исключений при нулевом числе
        обновлённых строк: отсутствие пригодных токенов для
        аннулирования является допустимым состоянием.
        """
        ...
