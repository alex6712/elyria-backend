"""Фейк асинхронного клиента Redis для unit-тестов.

Поддерживает подмножество команд, необходимое адаптерам
``src.shared.infrastructure.adapters.persistence``:

* ``set`` с параметрами ``ex`` и ``nx``;
* ``incr``;
* ``ttl``;
* ``exists``;
* группировку команд в pipeline.

Время жизни ключей моделируется виртуальными часами, управляемыми
методом :meth:`FakeRedisClient.advance`, что позволяет детерминированно
проверять поведение, зависящее от истечения времени.

Notes
-----
Реализация не преследует совместимость с Redis на уровне протокола
и покрывает только команды, используемые адаптерами проекта.
Команды группы pipeline выполняются последовательно, в порядке
добавления, поскольку именно такой порядок гарантирует Redis.
"""

from datetime import UTC, datetime, timedelta
from types import TracebackType
from typing import Self

_DEFAULT_NOW = datetime(2019, 4, 17, 6, 45, tzinfo=UTC)
"""Начальное значение виртуальных часов фейка."""


class FakeRedisPipeline:
    """Буфер команд pipeline, выполняемых в порядке добавления.

    Parameters
    ----------
    client : FakeRedisClient
        Клиент, выполняющий запланированные команды.
    """

    def __init__(self, client: FakeRedisClient) -> None:
        self._client = client
        self._commands: list[tuple[str, tuple[object, ...]]] = []

    def set(
        self,
        key: str,
        value: object,
        ex: int | None = None,
        nx: bool = False,
    ) -> Self:
        """Запланировать команду ``SET``."""
        self._commands.append(("set", (key, value, ex, nx)))
        return self

    def incr(self, key: str) -> Self:
        """Запланировать команду ``INCR``."""
        self._commands.append(("incr", (key,)))
        return self

    def ttl(self, key: str) -> Self:
        """Запланировать команду ``TTL``."""
        self._commands.append(("ttl", (key,)))
        return self

    async def execute(self) -> list[object]:
        """Выполнить накопленные команды и вернуть их результаты."""
        return [self._client.execute(name, args) for name, args in self._commands]

    async def reset(self) -> None:
        """Сбросить накопленные команды."""
        self._commands.clear()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._commands.clear()


class FakeRedisClient:
    """Минимальный in-memory клиент Redis для unit-тестов.

    Parameters
    ----------
    now : datetime, optional
        Начальное значение виртуальных часов.
    """

    def __init__(self, now: datetime | None = None) -> None:
        self._now = now or _DEFAULT_NOW
        self._values: dict[str, int] = {}
        self._ttls: dict[str, int] = {}
        self._expire_at: dict[str, datetime] = {}

    def advance(self, delta: timedelta) -> None:
        """Сдвинуть виртуальные часы вперёд.

        Parameters
        ----------
        delta : timedelta
            Величина сдвига виртуальных часов.
        """
        self._now += delta

    def keys(self) -> set[str]:
        """Вернуть множество не истёкших ключей, присутствующих в фейке.

        Returns
        -------
        set[str]
            Ключи, хранящиеся в текущий момент.
        """
        self._evict_expired()
        return set(self._values)

    def pipeline(self, transaction: bool = True) -> FakeRedisPipeline:  # noqa: ARG002
        """Вернуть pipeline для группировки команд.

        Parameters
        ----------
        transaction : bool, optional
            Признак транзакционности группы. Фейк не моделирует
            откат групп, поэтому параметр не используется.

        Returns
        -------
        FakeRedisPipeline
            Новый пустой pipeline.
        """
        return FakeRedisPipeline(self)

    def execute(self, name: str, args: tuple[object, ...]) -> object:
        """Выполнить команду и вернуть её результат.

        Parameters
        ----------
        name : str
            Имя команды: ``set``, ``incr``, ``ttl`` или ``exists``.
        args : tuple[object, ...]
            Аргументы команды.

        Returns
        -------
        object
            Результат выполнения команды.

        Raises
        ------
        ValueError
            Если команда не поддерживается фейком.
        """
        self._evict_expired()

        match name:
            case "set":
                key, value, ex, nx = args
                assert isinstance(key, str)
                assert isinstance(value, int)
                assert isinstance(ex, int | None)
                assert isinstance(nx, bool)

                if nx and key in self._values:
                    return None

                self._values[key] = value

                if ex is not None:
                    self._ttls[key] = ex
                    self._expire_at[key] = self._now + timedelta(seconds=ex)

                return True

            case "incr":
                (key,) = args
                assert isinstance(key, str)

                if key not in self._ttls:
                    self._ttls[key] = -1

                self._values[key] = self._values.get(key, 0) + 1
                return self._values[key]

            case "ttl":
                (key,) = args
                assert isinstance(key, str)

                if key not in self._values:
                    return -2

                expire_at = self._expire_at.get(key)
                if expire_at is None:
                    return -1

                return max(0, int((expire_at - self._now).total_seconds()))

            case "exists":
                (key,) = args
                assert isinstance(key, str)
                return int(key in self._values)

            case _:
                raise ValueError(f"Unsupported command: {name}.")

    def _evict_expired(self) -> None:
        for key in [k for k, moment in self._expire_at.items() if moment <= self._now]:
            del self._expire_at[key]
            _ = self._ttls.pop(key, None)
            _ = self._values.pop(key, None)
