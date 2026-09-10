import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


class InMemoryEventDispatcher:
    """Асинхронный диспетчер событий в памяти.

    Хранит обработчики во внутреннем словаре и вызывает их при отправке события.
    Обработчики одного типа события выполняются параллельно через `asyncio.gather`.
    Если хотя бы один из обработчиков выбрасывает исключение, оно агрегируется
    и пробрасывается после завершения всех задач.
    """

    def __init__(self) -> None:
        self._handlers: dict[Any, list[Callable[[Any], Awaitable[None]]]] = {}

    async def subscribe[T](
        self, event_type: type[T], handler: Callable[[T], Awaitable[None]]
    ) -> None:
        """Подписывает асинхронный обработчик на указанный тип события.

        Parameters
        ----------
        event_type : type[T]
            Класс или тип события, на который производится подписка.
        handler : Callable[[T], Awaitable[None]]
            Асинхронная функция, принимающая экземпляр ``event_type``
            и не возвращающая значения.

        Notes
        -----
        Если для данного типа события еще нет списка обработчиков,
        он создается автоматически. Порядок вызова обработчиков соответствует
        порядку их регистрации.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)

    async def publish(self, event: object) -> None:
        """Отправляет событие всем зарегистрированным обработчикам его типа.

        Обработчики вызываются одновременно. Исключения от отдельных
        обработчиков собираются и поднимаются единым исключением
        ``RuntimeError`` после завершения всех задач.

        Parameters
        ----------
        event : object
            Экземпляр события для рассылки.

        Raises
        ------
        RuntimeError
            Если один или несколько обработчиков выбросили исключения.
            Сообщение содержит текстовые представления всех агрегированных ошибок.
        """
        event_type = type(event)

        handlers = self._handlers.get(event_type, [])
        if not handlers:
            return

        results = await asyncio.gather(
            *[handler(event) for handler in handlers], return_exceptions=True
        )

        errors = [r for r in results if isinstance(r, BaseException)]
        if errors:
            raise RuntimeError(", ".join(str(err) for err in errors))
