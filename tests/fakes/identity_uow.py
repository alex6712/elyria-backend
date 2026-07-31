"""Фейковые реализации репозиториев и Unit of Work.

Позволяют тестировать Application Layer в изоляции: хранят сущности
в памяти, отслеживают вызовы, моделируют транзакционный откат и
нарушения контрактов (``UsernameAlreadyExistsError``,
``ConcurrentModificationError``).

Чтение возвращает копии сущностей (как загрузка строки из БД),
а записи фиксируют изменения в хранилище, что позволяет
воспроизводить конкурентные сценарии optimistic locking.
"""

from datetime import datetime
from types import TracebackType
from uuid import UUID

from src.identity.domain.entities import Identity, Profile, Session
from src.identity.domain.exceptions import UsernameAlreadyExistsError
from src.identity.domain.value_objects import Username
from src.shared.application.exception import UnitOfWorkNotEnteredError
from src.shared.domain.exceptions import ConcurrentModificationError


class FakeIdentityRepository:
    """Фейк репозитория учётных записей.

    Хранит сущности :class:`Identity` в памяти. При вставке дубликата
    ``username`` выбрасывает :class:`UsernameAlreadyExistsError` в
    соответствии с контрактом порта. Метод ``save_password_hash``
    проверяет версию агрегата и выбрасывает
    :class:`ConcurrentModificationError` при расхождении.

    Attributes
    ----------
    added : list[Identity]
        Зарегистрированные сущности в порядке вызова ``add``.
    fail_on_add : Exception | None
        Исключение, выбрасываемое методом ``add`` при каждом вызове.
    """

    def __init__(self) -> None:
        self._identities: dict[UUID, Identity] = {}
        self.added: list[Identity] = []
        self.fail_on_add: Exception | None = None

    async def add(self, identity: Identity) -> None:
        """Сохранить учётную запись, контролируя уникальность username.

        Parameters
        ----------
        identity : Identity
            Сохраняемая учётная запись.

        Raises
        ------
        UsernameAlreadyExistsError
            Если ``username`` уже занят другой учётной записью.
        """
        if self.fail_on_add is not None:
            raise self.fail_on_add

        if any(
            stored.username == identity.username for stored in self._identities.values()
        ):
            raise UsernameAlreadyExistsError(
                f"User with username={identity.username} already exists."
            )

        self._identities[identity.id] = identity
        self.added.append(identity)

    async def get_by_id(self, id: UUID) -> Identity | None:
        """Получить учётную запись по идентификатору (копию)."""
        stored = self._identities.get(id)
        return self._copy(stored) if stored is not None else None

    async def get_by_username(self, username: Username) -> Identity | None:
        """Получить учётную запись по имени пользователя (копию)."""
        for stored in self._identities.values():
            if stored.username == username:
                return self._copy(stored)

        return None

    async def save_password_hash(self, identity: Identity) -> None:
        """Сохранить хэш пароля с проверкой версии агрегата.

        Parameters
        ----------
        identity : Identity
            Учётная запись с изменённым хэшем пароля.

        Raises
        ------
        ConcurrentModificationError
            Если версия сущности не совпадает с версией в хранилище.
        """
        stored = self._identities.get(identity.id)

        if stored is None or stored.version != identity.version:
            raise ConcurrentModificationError(identity.id, "Identity")

        stored.password_hash = identity.password_hash
        stored.updated_at = identity.updated_at
        stored.upgrade()
        identity.upgrade()

    def rollback_to(self, count: int) -> None:
        """Удалить добавления, выполненные после указанного количества.

        Имитирует откат транзакции для вставок, выполненных в рамках
        текущей единицы работы.
        """
        for entity in self.added[count:]:
            self._identities.pop(entity.id, None)

        del self.added[count:]

    @staticmethod
    def _copy(identity: Identity) -> Identity:
        """Создать независимую копию учётной записи (как строку из БД)."""
        return Identity(
            id=identity.id,
            username=identity.username,
            password_hash=identity.password_hash,
            is_active=identity.is_active,
            version=identity.version,
            created_at=identity.created_at,
            updated_at=identity.updated_at,
        )


class FakeProfileRepository:
    """Фейк репозитория профилей пользователей.

    Attributes
    ----------
    added : list[Profile]
        Зарегистрированные профили в порядке вызова ``add``.
    fail_on_add : Exception | None
        Исключение, выбрасываемое методом ``add`` при каждом вызове.
    """

    def __init__(self) -> None:
        self._profiles: dict[UUID, Profile] = {}
        self.added: list[Profile] = []
        self.fail_on_add: Exception | None = None

    async def add(self, profile: Profile) -> None:
        """Сохранить профиль пользователя."""
        if self.fail_on_add is not None:
            raise self.fail_on_add

        self._profiles[profile.id] = profile
        self.added.append(profile)

    async def get_by_identity_id(self, identity_id: UUID) -> Profile | None:
        """Получить профиль по идентификатору учётной записи (копию)."""
        for stored in self._profiles.values():
            if stored.identity_id == identity_id:
                return self._copy(stored)

        return None

    async def save_display_name(self, profile: Profile) -> None:
        """Сохранить отображаемое имя с проверкой версии агрегата.

        Raises
        ------
        ConcurrentModificationError
            Если версия сущности не совпадает с версией в хранилище.
        """
        stored = self._profiles.get(profile.id)

        if stored is None or stored.version != profile.version:
            raise ConcurrentModificationError(profile.id, "Profile")

        stored.display_name = profile.display_name
        stored.updated_at = profile.updated_at
        stored.upgrade()
        profile.upgrade()

    def rollback_to(self, count: int) -> None:
        """Удалить добавления, выполненные после указанного количества."""
        for entity in self.added[count:]:
            self._profiles.pop(entity.id, None)

        del self.added[count:]

    @staticmethod
    def _copy(profile: Profile) -> Profile:
        """Создать независимую копию профиля (как строку из БД)."""
        return Profile(
            id=profile.id,
            identity_id=profile.identity_id,
            display_name=profile.display_name,
            avatar_url=profile.avatar_url,
            version=profile.version,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )


class FakeSessionRepository:
    """Фейк репозитория пользовательских сессий.

    Attributes
    ----------
    added : list[Session]
        Добавленные сессии в порядке вызова ``add``.
    rotation_calls : list[Session]
        Сессии, переданные в ``save_rotation``.
    revocation_calls : list[Session]
        Сессии, переданные в ``save_revocation``.
    fail_on_add : Exception | None
        Исключение, выбрасываемое методом ``add`` при каждом вызове.
    fail_on_save_rotation : Exception | None
        Исключение, выбрасываемое методом ``save_rotation``.
    fail_on_save_revocation : Exception | None
        Исключение, выбрасываемое методом ``save_revocation``.
    """

    def __init__(self) -> None:
        self._sessions: dict[UUID, Session] = {}
        self.added: list[Session] = []
        self.rotation_calls: list[Session] = []
        self.revocation_calls: list[Session] = []
        self.fail_on_add: Exception | None = None
        self.fail_on_save_rotation: Exception | None = None
        self.fail_on_save_revocation: Exception | None = None

    async def add(self, session: Session) -> None:
        """Сохранить сессию."""
        if self.fail_on_add is not None:
            raise self.fail_on_add

        self._sessions[session.id] = session
        self.added.append(session)

    async def get_by_id(self, id: UUID) -> Session | None:
        """Получить сессию по идентификатору (копию)."""
        stored = self._sessions.get(id)
        return self._copy(stored) if stored is not None else None

    async def get_by_session_secret(self, session_secret: str) -> Session | None:
        """Получить сессию по секрету сессии (копию)."""
        for stored in self._sessions.values():
            if stored.session_secret == session_secret:
                return self._copy(stored)

        return None

    async def mark_used(self, id: UUID, at: datetime) -> bool:
        """Зафиксировать факт использования сессии.

        Returns
        -------
        bool
            ``True``, если сессия найдена и время обновлено.
        """
        session = self._sessions.get(id)

        if session is None:
            return False

        session.last_used_at = at
        return True

    async def save_rotation(self, session: Session) -> None:
        """Сохранить ротацию секрета с проверкой версии агрегата.

        Raises
        ------
        ConcurrentModificationError
            Если версия сущности не совпадает с версией в хранилище.
        """
        if self.fail_on_save_rotation is not None:
            raise self.fail_on_save_rotation

        stored = self._sessions.get(session.id)

        if stored is None or stored.version != session.version:
            raise ConcurrentModificationError(session.id, "Session")

        stored.session_secret = session.session_secret
        stored.expires_at = session.expires_at
        stored.updated_at = session.updated_at
        stored.upgrade()
        session.upgrade()
        self.rotation_calls.append(session)

    async def save_revocation(self, session: Session) -> None:
        """Сохранить отзыв сессии с проверкой версии агрегата.

        Raises
        ------
        ConcurrentModificationError
            Если версия сущности не совпадает с версией в хранилище.
        """
        if self.fail_on_save_revocation is not None:
            raise self.fail_on_save_revocation

        stored = self._sessions.get(session.id)

        if stored is None or stored.version != session.version:
            raise ConcurrentModificationError(session.id, "Session")

        stored.revoked_at = session.revoked_at
        stored.updated_at = session.updated_at
        stored.upgrade()
        session.upgrade()
        self.revocation_calls.append(session)

    async def revoke_all_by_identity_id(self, identity_id: UUID) -> int:
        """Отозвать все сессии учётной записи.

        Returns
        -------
        int
            Количество отозванных сессий.
        """
        revoked_count = 0

        for session in self._sessions.values():
            if session.identity_id == identity_id and not session.is_revoked():
                session.revoke()
                revoked_count += 1

        return revoked_count

    def rollback_to(self, count: int) -> None:
        """Удалить добавления, выполненные после указанного количества."""
        for entity in self.added[count:]:
            self._sessions.pop(entity.id, None)

        del self.added[count:]

    @staticmethod
    def _copy(session: Session) -> Session:
        """Создать независимую копию сессии (как строку из БД)."""
        return Session(
            id=session.id,
            identity_id=session.identity_id,
            session_secret=session.session_secret,
            expires_at=session.expires_at,
            last_used_at=session.last_used_at,
            revoked_at=session.revoked_at,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            version=session.version,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )


class FakeIdentityUnitOfWork:
    """Фейк :class:`IdentityUnitOfWork` с репозиториями в памяти.

    Ведёт счёт вызовов ``commit``/``rollback``, выполняемых при
    завершении асинхронного контекста, и контролирует вход в
    единицу работы: обращение к свойствам-репозиториям вне
    контекста выбрасывает :class:`UnitOfWorkNotEnteredError`.
    Сами репозитории доступны через публичные атрибуты
    ``identity_repo``, ``profile_repo``, ``session_repo`` для
    настройки состояния и проверки результатов тестов.

    При завершении контекста с исключением откатывает вставки,
    выполненные в рамках текущей единицы работы.

    Attributes
    ----------
    identity_repo : FakeIdentityRepository
        Репозиторий учётных записей (без проверки входа).
    profile_repo : FakeProfileRepository
        Репозиторий профилей (без проверки входа).
    session_repo : FakeSessionRepository
        Репозиторий сессий (без проверки входа).
    commit_count : int
        Количество автоматических коммитов (успешных выходов).
    rollback_count : int
        Количество автоматических откатов (выходов с исключением).
    """

    def __init__(
        self,
        *,
        identities: FakeIdentityRepository | None = None,
        profiles: FakeProfileRepository | None = None,
        sessions: FakeSessionRepository | None = None,
    ) -> None:
        self.identity_repo = identities or FakeIdentityRepository()
        self.profile_repo = profiles or FakeProfileRepository()
        self.session_repo = sessions or FakeSessionRepository()

        self._entered = False
        self.commit_count = 0
        self.rollback_count = 0
        self._added_counts: dict[object, int] = {}

    @property
    def identities(self) -> FakeIdentityRepository:
        """Репозиторий учётных записей (только внутри контекста)."""
        self._ensure_entered()
        return self.identity_repo

    @property
    def profiles(self) -> FakeProfileRepository:
        """Репозиторий профилей (только внутри контекста)."""
        self._ensure_entered()
        return self.profile_repo

    @property
    def sessions(self) -> FakeSessionRepository:
        """Репозиторий сессий (только внутри контекста)."""
        self._ensure_entered()
        return self.session_repo

    def _ensure_entered(self) -> None:
        if not self._entered:
            raise UnitOfWorkNotEnteredError(
                "IdentityUnitOfWork must be entered before use."
            )

    async def commit(self) -> None:
        """Зафиксировать единицу работы (ручной вызов)."""
        self._ensure_entered()
        self.commit_count += 1

    async def rollback(self) -> None:
        """Отменить единицу работы (ручной вызов)."""
        self._ensure_entered()
        self.rollback_count += 1

    async def __aenter__(self) -> FakeIdentityUnitOfWork:
        self._entered = True
        self._added_counts = {
            self.identity_repo: len(self.identity_repo.added),
            self.profile_repo: len(self.profile_repo.added),
            self.session_repo: len(self.session_repo.added),
        }
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc is None:
            self.commit_count += 1
        else:
            self.rollback_count += 1
            self.identity_repo.rollback_to(self._added_counts[self.identity_repo])
            self.profile_repo.rollback_to(self._added_counts[self.profile_repo])
            self.session_repo.rollback_to(self._added_counts[self.session_repo])

        self._entered = False
