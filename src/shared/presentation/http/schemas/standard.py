from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from src.shared.presentation.http import APICode


class BaseJsonModel(BaseModel):
    """Базовая модель данных, сериализуемых в JSON.

    Предоставляет общую конфигурацию Pydantic-моделей,
    используемых для представления данных в JSON API.

    Для имён полей используется преобразование из ``snake_case``
    в ``camelCase`` при сериализации. При этом модель также
    принимает значения, переданные по исходным именам полей
    в формате ``snake_case``.

    Это позволяет использовать стандартное для Python соглашение
    об именовании полей внутри приложения, сохраняя
    ``camelCase``-представление на границе HTTP API.

    Notes
    -----
    Генератор псевдонимов ``to_camel`` применяется ко всем полям
    производных моделей, если для конкретного поля явно не задан
    собственный alias.

    Examples
    --------
    Для поля ``created_at``:

    .. code-block:: python
        class UserResponse(BaseJsonModel):
            created_at: datetime

    модель допускает заполнение по имени поля:

    .. code-block:: python
        UserResponse(created_at=value)

    а при сериализации с использованием alias получает имя:

    .. code-block:: python
        {"createdAt": ...}

    See Also
    --------
    :class:`pydantic.BaseModel`
        Базовый класс Pydantic-моделей.
    :func:`pydantic.alias_generators.to_camel`
        Генератор camelCase-псевдонимов.
    """

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class StandardResponse(BaseJsonModel):
    """Стандартная модель ответа сервера.

    Используется в качестве базовой модели ответа для HTTP API.
    Каждый стандартный ответ содержит код результата операции
    в поле ``code`` и сообщение в поле ``detail``.

    Производные модели могут расширять эту модель дополнительными
    полями, сохраняя общий формат ответа.

    Attributes
    ----------
    code : APICode
        Код результата операции в соответствии с перечислением
        ``APICode``.
    detail : str
        Сообщение с описанием результата операции.

    See Also
    --------
    :class:`BaseJsonModel`
        Базовая JSON-модель с общей конфигурацией Pydantic.
    :class:`APICode`
        Перечисление кодов API.
    """

    code: APICode = Field(
        default=APICode.SUCCESS,
        description="Код результата операции в виде перечисления APICode.",
        examples=[APICode.SUCCESS, APICode.TOKEN_NOT_PASSED],
    )
    detail: str = Field(
        default="Success!",
        description="Сообщение с описанием результата операции.",
        examples=[
            "Success!",
            "Access token is missing. Provide it in the "
            + "Authorization: Bearer <token> header.",
        ],
    )


class CountResponse(StandardResponse):
    """Модель ответа сервера с количеством записей.

    Используется для эндпоинтов, возвращающих общее количество
    записей некоторой сущности.

    Attributes
    ----------
    count : int
        Общее количество записей.
    """

    count: int = Field(description="Общее количество записей.")


class PaginationResponse(StandardResponse):
    """Модель ответа сервера с общим количеством записей для пагинации.

    Используется для ответов эндпоинтов, возвращающих списки данных
    с пагинацией, когда клиенту дополнительно требуется общее
    количество доступных записей.

    Attributes
    ----------
    total : int
        Общее количество записей, доступных пользователю.
    """

    total: int = Field(description="Общее количество записей, доступных пользователю.")
