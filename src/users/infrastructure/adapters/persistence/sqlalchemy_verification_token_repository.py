from datetime import datetime
from uuid import UUID

from sqlalchemy import RowMapping, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from src.users.domain.entities import VerificationToken
from src.users.domain.value_objects import VerificationTokenPurpose
from src.users.infrastructure.tables import verification_tokens_table


class SqlAlchemyVerificationTokenRepository:
    """Репозиторий токенов подтверждения на основе SQLAlchemy Core.

    Реализует операции сохранения, получения и аннулирования
    доменной сущности ``VerificationToken`` над таблицей
    ``verification_tokens``.

    Parameters
    ----------
    connection : AsyncConnection
        Асинхронное подключение к базе данных SQLAlchemy.

    Notes
    -----
    Удовлетворяет протоколу ``VerificationTokenRepository``
    структурно (duck typing) без явного наследования.
    """

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def add(self, token: VerificationToken) -> None:
        """Сохранить новый токен подтверждения в базу данных.

        Выполняет вставку записи в таблицу ``verification_tokens``.
        Метка создания записи передаётся из доменной сущности явно.

        Parameters
        ----------
        token : VerificationToken
            Доменная сущность токена для сохранения.
        """
        _ = await self._connection.execute(
            insert(verification_tokens_table).values(
                id=token.id,
                identity_id=token.identity_id,
                token_hash=token.token_hash,
                purpose=token.purpose.value,
                expires_at=token.expires_at,
                used_at=token.used_at,
                created_at=token.created_at,
                updated_at=token.updated_at,
            )
        )

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
        result = await self._connection.execute(
            select(verification_tokens_table).where(
                verification_tokens_table.c.token_hash == token_hash
            )
        )

        if not (row := result.mappings().first()):
            return None

        return self._row_to_verification_token(row)

    async def invalidate_active_by_identity_id(
        self,
        identity_id: UUID,
        purpose: VerificationTokenPurpose,
        *,
        at: datetime,
    ) -> None:
        """Аннулировать пригодные токены учётной записи.

        Одним атомарным обновлением переводит в непригодное
        состояние все токены указанной учётной записи с заданным
        назначением, которые ещё не были применены или
        аннулированы.

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
        Отсутствие пригодных токенов для аннулирования не является
        ошибкой: при нулевом числе обновлённых строк исключение
        не возбуждается.
        """
        _ = await self._connection.execute(
            update(verification_tokens_table)
            .values(used_at=at, updated_at=at)
            .where(
                verification_tokens_table.c.identity_id == identity_id,
                verification_tokens_table.c.purpose == purpose,
                verification_tokens_table.c.used_at.is_(None),
            )
        )

    @staticmethod
    def _row_to_verification_token(row: RowMapping) -> VerificationToken:
        """Преобразовать строку результата запроса в доменную сущность.

        Parameters
        ----------
        row : RowMapping
            Строка результата запроса (mapping).

        Returns
        -------
        VerificationToken
            Доменная сущность токена подтверждения.
        """
        return VerificationToken(
            id=row["id"],
            identity_id=row["identity_id"],
            token_hash=row["token_hash"],
            purpose=VerificationTokenPurpose(row["purpose"]),
            expires_at=row["expires_at"],
            used_at=row["used_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
