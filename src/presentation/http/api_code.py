from enum import StrEnum


class APICode(StrEnum):
    """Класс-перечисление для представления кодов ответов API.

    Представляет собой единое перечисление всех возможных
    ответов API с их описанием и use cases.

    Attributes
    ----------
    SUCCESS
        Успех.
    I_AM_A_TEAPOT
        Я - чайник.
    RESOURCE_NOT_FOUND
        Ресурс не найден.
    VALIDATION_ERROR
        Неверные данные.
    NOTHING_TO_UPDATE
        Пустой PATCH-запрос.
    INCORRECT_USERNAME_PASSWORD
        Неверное имя пользователя или пароль.
    INCORRECT_PASSWORD
        Текущий пароль не совпадает с сохранённым в БД.
    NEW_PASSWORD_SAME_AS_OLD
        Новый пароль совпадает с текущим сохранённым в БД.
    PASSWORD_UPDATE_FAILED
        Обновление пароля не затронуло ни одной строки в БД.
    TOKEN_NOT_PASSED
        Токен не передан.
    INVALID_TOKEN
        Неверный токен.
    TOKEN_SIGNATURE_EXPIRED
        Подпись токена просрочена.
    TOKEN_REVOKED
        Токен отозван.
    INVALID_IDEMPOTENCY_KEY
        Неверный формат ключа идемпотентности.
    IDEMPOTENCY_CONFLICT
        Запрос уже в обработке.
    UNIQUE_CONFLICT
        Конфликт уникальности.
    COUPLE_NOT_SELF
        Запрещена пользовательская пара с самим собой.
    ALBUM_NOT_FOUND
        Медиа-альбом не найден.
    FILE_NOT_FOUND
        Медиа-файл не найден.
    FILE_UPLOAD_PENDING
        Файл ещё не загружен в хранилище.
    FILE_UPLOAD_FAILED
        Загрузка файла завершилась ошибкой.
    FILE_DELETED
        Файл был удалён пользователем.
    FILE_PRESIGNED_URL_GENERATION_FAILED
        Ошибка при генерации presigned URL.
    UNSUPPORTED_FILE_TYPE
        Не поддерживаемый тип файла.
    UPLOAD_NOT_COMPLETED
        ФАйл не найден в объектном хранилище.
    RATE_LIMIT_EXCEEDED
        Превышено максимальное количество запросов за единицу времени.
    INTERNAL_SERVER_ERROR
        Внутренняя ошибка сервера.
    """

    SUCCESS = "SUCCESS"
    """Когда всё хорошо, ничего не сломалось, а пользователь - молодец."""

    I_AM_A_TEAPOT = "I_AM_A_TEAPOT"
    """Я - чайник и не могу сварить кофе."""

    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    """При попытке доступа к несуществующему ресурсу."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    """При ошибке валидации переданных клиентом данных."""

    NOTHING_TO_UPDATE = "NOTHING_TO_UPDATE"
    """Вызывается, когда PATCH-запрос не содержит ни одного поля для обновления - 
    все поля DTO остались `UNSET`."""

    INCORRECT_USERNAME_PASSWORD = "INCORRECT_USERNAME_PASSWORD"
    """Если по `username` не найден пользователь или `password` и хеш пароля в БД не совпадают."""

    INCORRECT_PASSWORD = "INCORRECT_PASSWORD"
    """Текущий пароль не совпадает с сохранённым в БД."""

    NEW_PASSWORD_SAME_AS_OLD = "NEW_PASSWORD_SAME_AS_OLD"
    """Новый пароль совпадает с текущим сохранённым в БД."""

    PASSWORD_UPDATE_FAILED = "PASSWORD_UPDATE_FAILED"
    """Обновление пароля не затронуло ни одной строки в БД."""

    TOKEN_NOT_PASSED = "TOKEN_NOT_PASSED"
    """Вызывается при условии, что JWT не передан в заголовках запроса."""

    INVALID_TOKEN = "INVALID_TOKEN"
    """Неверный токен.

    Используется в случаях:
    1. Если в `payload` токена отсутствует хотя бы один из ключей `sub` и `exp`;
    2. если значение по ключу `sub` (user_id) не существует в БД;
    3. не получается проверить подпись токена (подпись токена недействительна);
    4. переданный токен обновления не совпадает с хешем в БД.
    """

    TOKEN_SIGNATURE_EXPIRED = "TOKEN_SIGNATURE_EXPIRED"
    """Подпись токена действительна, однако вышло время жизни токена."""

    TOKEN_REVOKED = "TOKEN_REVOKED"
    """Если переданный клиентом токен был отозван и находится в чёрном списке."""

    INVALID_IDEMPOTENCY_KEY = "INVALID_IDEMPOTENCY_KEY"
    """Ключ идемпотентности не совпадает с ожидаемый форматом (UUIDv4)."""

    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    """Запрос по предоставленному ключу идемпотентности уже обрабатывается."""

    UNIQUE_CONFLICT = "UNIQUE_CONFLICT"
    """При попытке создать новую запись по уже существующему уникальному ключу."""

    COUPLE_NOT_SELF = "COUPLE_NOT_SELF"
    """При попытке создать пользовательскую пару с самим собой."""

    ALBUM_NOT_FOUND = "ALBUM_NOT_FOUND"
    """При попытке получить медиаальбом по несуществующему набору параметров."""

    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    """При попытке получить медиафайл по несуществующему набору параметров."""

    FILE_UPLOAD_PENDING = "FILE_UPLOAD_PENDING"
    """При попытке скачать файл, загрузка которого ещё не завершена (статус PENDING)."""

    FILE_UPLOAD_FAILED = "FILE_UPLOAD_FAILED"
    """При попытке скачать файл, загрузка которого завершилась ошибкой (статус FAILED)."""

    FILE_DELETED = "FILE_DELETED"
    """При попытке скачать файл, который был явно удалён пользователем (статус DELETED)."""

    FILE_PRESIGNED_URL_GENERATION_FAILED = "FILE_PRESIGNED_URL_GENERATION_FAILED"
    """Presigned URL для загрузки/скачивания файла не была сгенерирована из-за ошибки."""

    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    """При попытке загрузить файл с необрабатываемым типом."""

    UPLOAD_NOT_COMPLETED = "UPLOAD_NOT_COMPLETED"
    """При подтверждении клиентом загрузки файл, файл не найден в объектном хранилище."""

    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    """Превышено максимальное количество запросов за единицу времени."""

    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    """На сервере произошла неожиданная ошибка. В любом случае, клиент не должен знать какая."""
