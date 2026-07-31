"""Фейки SQLAlchemy: соединение и результаты запросов."""


class FakeDBAPIError(Exception):
    """Имитация низкоуровневой ошибки драйвера БД."""


class FakeResult:
    """Имитация результата выполнения SQL-запроса."""

    def __init__(self, row: dict | None = None, rowcount: int = 1) -> None:
        self._row = row
        self.rowcount = rowcount

    def mappings(self) -> FakeResult:
        """Вернуть себя как контейнер mapping-строк."""
        return self

    def first(self) -> dict | None:
        """Вернуть первую строку."""
        return self._row


class FakeConnection:
    """Имитация AsyncConnection, записывающая выполненные запросы."""

    def __init__(self) -> None:
        self.executed: list = []
        self.result: FakeResult = FakeResult()
        self.error: Exception | None = None

    async def execute(self, stmt):
        """Записать запрос и вернуть настроенный результат."""
        self.executed.append(stmt)

        if self.error is not None:
            raise self.error

        return self.result
