from typing import Protocol, runtime_checkable
from uuid import UUID

from src.domain.iam.entities import Identity


@runtime_checkable
class IdentityRepository(Protocol):
    """Порт репозитория учётных записей (identity).

    Определяет контракт для операций сохранения и получения
    учётных записей системы. Расширяет базовый репозиторий
    методом добавления новой учётной записи.
    """

    async def add(self, identity: Identity) -> None:
        """Сохранить новую учётную запись.

        Parameters
        ----------
        identity : Identity
            Доменная сущность учётной записи для сохранения.

        Raises
        ------
        AlreadyExistsException
            Если учётная запись с таким идентификатором уже существует.
        """
        ...

    async def get_by_id(self, id: UUID) -> Identity: ...
