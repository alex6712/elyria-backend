import logging

from sqlalchemy.ext.asyncio import AsyncEngine

from src.users.application.dto.read_models import UserSearchReadModel
from src.users.domain.events import ProfileChangedEvent, UserRegisteredEvent
from src.users.infrastructure.adapters.readers import SqlAlchemyUserSearchReader

logger = logging.getLogger(__name__)
"""Модульный логгер для обработчика проекции поиска пользователей."""


class UserSearchProjection:
    """Обработчик проекции поиска пользователей по имени пользователя.

    Подписывается на доменные события :class:`UserRegisteredEvent`
    и :class:`ProfileChangedEvent` и синхронизирует denormalized
    read model (таблицу ``user_search_read_model``) с источниками
    (учётными записями и профилями).

    В соответствии с ADR-0002 read model обновляется ПОСЛЕ успешного
    коммита основной транзакции в собственном соединении
    (отдельной транзакции), обеспечивая eventual consistency.
    Ошибки обновления read model не влияют на успешный результат
    основной операции: они логируются для последующего восстановления
    (partial success пост-коммитных независимых операций допустим).

    Parameters
    ----------
    engine : AsyncEngine
        Асинхронный движок SQLAlchemy для открытия собственного
        соединения и транзакции обновления read model.
    """

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def handle_user_registered(self, event: UserRegisteredEvent) -> None:
        """Обработать событие регистрации пользователя.

        Создаёт либо обновляет строку read model для новой учётной записи.

        Parameters
        ----------
        event : UserRegisteredEvent
            Событие регистрации новой учётной записи и профиля.
        """
        await self._upsert(
            UserSearchReadModel(
                identity_id=event.identity_id,
                profile_id=event.profile_id,
                username=event.username,
                display_name=event.display_name,
                avatar_url=event.avatar_url,
            )
        )

    async def handle_profile_changed(self, event: ProfileChangedEvent) -> None:
        """Обработать событие изменения профиля.

        Обновляет строку read model для изменённого профиля.

        Parameters
        ----------
        event : ProfileChangedEvent
            Событие изменения отображаемого имени и/или аватара профиля.
        """
        await self._upsert(
            UserSearchReadModel(
                identity_id=event.identity_id,
                profile_id=event.profile_id,
                username=event.username,
                display_name=event.display_name,
                avatar_url=event.avatar_url,
            )
        )

    async def _upsert(self, read_model: UserSearchReadModel) -> None:
        """Записать read model в собственную транзакцию.

        Открывает отдельное соединение и транзакцию, выполняет
        upsert строки read model. Ошибки логируются и не пробрасываются
        наверх, сохраняя успешный результат основной операции.

        Parameters
        ----------
        read_model : UserSearchReadModel
            Денормализованные данные учётной записи и профиля.
        """
        try:
            async with self._engine.connect() as connection, connection.begin():
                await SqlAlchemyUserSearchReader(connection).upsert(read_model)
        except Exception:
            logger.exception(
                "Failed to update user search read_model for identity=%s",
                read_model.identity_id,
            )
