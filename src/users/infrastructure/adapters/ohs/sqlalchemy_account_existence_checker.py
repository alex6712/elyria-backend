from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncEngine

from src.users.infrastructure.tables import identities_table


class SqlAlchemyAccountExistenceChecker:
    """SQLAlchemy-реализация проверки существования активных учётных записей.

    Реализует контракт OHS контекста Users
    (:class:`~src.shared.application.ohs.users.AccountExistenceChecker`):
    позволяет другим bounded contexts выяснить, какие из переданных
    идентификаторов не соответствуют состоянию "существует и активна".

    Проверка выполняется в собственном коротком соединении, открываемом
    на время вызова, без присоединения к транзакции вызывающей стороны.
    Источником истины служит таблица ``identities`` (write-модель),
    а не отложенные read model.

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy для открытия read-соединений.
    """

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def which_do_not_exist(self, identity_ids: Sequence[UUID]) -> list[UUID]:
        """Определить идентификаторы учётных записей, которых нет.

        Открывает собственное соединение и выполняет запрос на получение
        идентификаторов тех учётных записей, чьи идентификаторы
        представлены в аргументе и при этом являются активными.
        Возвращает список идентификаторов, не полученных в результате запроса.

        Parameters
        ----------
        identity_ids : Sequence[UUID]
            Идентификаторы учётных записей для проверки.

        Returns
        -------
        list[UUID]
            Идентификаторы, для которых активной учётной записи
            не существует, в порядке следования во входной
            последовательности. Пустой список, если все записи
            существуют и активны.
        """
        if not identity_ids:
            return []

        async with self._engine.connect() as connection:
            result = await connection.execute(
                select(identities_table.c.id).where(
                    and_(
                        identities_table.c.id.in_(identity_ids),
                        identities_table.c.is_active.is_(True),
                    )
                )
            )

            found_ids = {UUID(r["id"]) for r in result.mappings().all()}

            return [
                identity_id
                for identity_id in identity_ids
                if identity_id not in found_ids
            ]
