"""Фейки репозиториев и Unit of Work для unit-тестов.

Инкапсулируют in-memory имплементации ``IdentityRepository``,
``ProfileRepository``, ``SessionRepository`` и ``UsersUnitOfWork``.

Реализуют key invariant: ``add`` проверяет уникальность username
и email, а ``save_*`` (optimistic locking) проверяет версию
агрегата ``IdentityRepository``.
"""

from copy import deepcopy
from types import TracebackType
from uuid import UUID

from src.shared.domain.exceptions import ConcurrentModificationError
from src.users.application.dto.read_models import UserSearchReadModel
from src.users.domain.entities import Identity, Profile, Session
from src.users.domain.exceptions import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from src.users.domain.value_objects import Username


class FakeIdentityRepository:
    """In-memory репозиторий ``Identity`` с проверкой уникальности."""

    def __init__(self) -> None:
        self._rows: dict[UUID, Identity] = {}
        self.added: list[Identity] = []
        self._rollback_to_count: int = 0

    async def add(self, identity: Identity) -> None:
        for existing in self._rows.values():
            if existing.username.value == identity.username.value:
                raise UsernameAlreadyExistsError(
                    f"User with username={identity.username} already exists."
                )
            if existing.email.value == identity.email.value:
                raise EmailAlreadyExistsError(
                    f"User with email={identity.email} already exists."
                )

        self.added.append(deepcopy(identity))
        self._rows[identity.id] = deepcopy(identity)

    async def get_by_id(self, id: UUID) -> Identity | None:
        row = self._rows.get(id)
        return deepcopy(row) if row is not None else None

    async def get_by_username(self, username: Username) -> Identity | None:
        for row in self._rows.values():
            if row.username.value == username.value:
                return deepcopy(row)
        return None

    async def save_password_hash(self, identity: Identity) -> None:
        existing = self._rows.get(identity.id)

        if existing is None or existing.version != identity.version:
            raise ConcurrentModificationError(identity.id, "Identity")

        updated = deepcopy(identity)
        updated.version += 1
        self._rows[identity.id] = updated
        identity.upgrade()

    def rollback_to(self, count: int) -> None:
        self._rollback_to_count = count
        removed = self.added[count:]
        for r in removed:
            del self._rows[r.id]
        self.added = self.added[:count]


class FakeProfileRepository:
    """In-memory репозиторий ``Profile``."""

    def __init__(self) -> None:
        self._rows: dict[UUID, Profile] = {}
        self.added: list[Profile] = []

    async def add(self, profile: Profile) -> None:
        self.added.append(deepcopy(profile))
        self._rows[profile.id] = deepcopy(profile)

    async def get_by_id(self, profile_id: UUID) -> Profile | None:
        row = self._rows.get(profile_id)
        return deepcopy(row) if row is not None else None

    async def get_by_identity_id(self, identity_id: UUID) -> Profile | None:
        for row in self._rows.values():
            if row.identity_id == identity_id:
                return deepcopy(row)
        return None

    async def save_profile_changes(self, profile: Profile) -> None:
        existing = self._rows.get(profile.id)

        if existing is None or existing.version != profile.version:
            raise ConcurrentModificationError(profile.id, "Profile")

        updated = deepcopy(profile)
        updated.version += 1
        self._rows[profile.id] = updated
        profile.upgrade()


class FakeSessionRepository:
    """In-memory репозиторий ``Session``."""

    def __init__(self) -> None:
        self._rows: dict[UUID, Session] = {}
        self.added: list[Session] = []
        self.refresh_calls: list[Session] = []
        self.revocation_calls: list[Session] = []

    async def add(self, session: Session) -> None:
        self.added.append(deepcopy(session))
        self._rows[session.id] = deepcopy(session)

    async def get_by_id(self, id: UUID) -> Session | None:
        row = self._rows.get(id)
        return deepcopy(row) if row is not None else None

    async def get_by_session_secret(self, session_secret: str) -> Session | None:
        for row in self._rows.values():
            if row.session_secret == session_secret:
                return deepcopy(row)
        return None

    async def save_refresh(self, session: Session) -> None:
        existing = self._rows.get(session.id)

        if existing is None or existing.version != session.version:
            raise ConcurrentModificationError(session.id, "Session")

        self.refresh_calls.append(deepcopy(session))
        updated = deepcopy(session)
        updated.version += 1
        self._rows[session.id] = updated
        session.upgrade()

    async def save_revocation(self, session: Session) -> None:
        existing = self._rows.get(session.id)

        if existing is None or existing.version != session.version:
            raise ConcurrentModificationError(session.id, "Session")

        self.revocation_calls.append(deepcopy(session))
        updated = deepcopy(session)
        updated.version += 1
        self._rows[session.id] = updated
        session.upgrade()

    async def revoke_all_by_identity_id(
        self, identity_id: UUID, *, except_session_id: UUID | None = None
    ) -> int:
        count = 0
        for row in self._rows.values():
            if (
                row.identity_id == identity_id
                and row.id != except_session_id
                and row.revoked_at is None
            ):
                row.revoked_at = row.created_at
                count += 1
        return count


class FakeUserSearchReader:
    """Фейк reader поиска пользователей (не используется в этих тестах)."""

    async def upsert(self, read_model: UserSearchReadModel) -> None:
        pass

    async def search_by_username(
        self,
        query: str,  # noqa: ARG002
        limit: int,  # noqa: ARG002
        offset: int,  # noqa: ARG002
    ) -> list[UserSearchReadModel]:
        return []

    async def count_by_username(self, query: str) -> int:  # noqa: ARG002
        return 0


class FakeUsersUnitOfWork:
    """In-memory ``UsersUnitOfWork`` для unit-тестов.

    Реализует ``async with`` семантику. При успешном завершении
    (нет исключений) транзакция считается зафиксированной;
    при исключении -- отменённой. Откат восстанавливает
    состояние ``add``-списков репозиториев через ``rollback_to``.
    """

    def __init__(self) -> None:
        self.commit_count: int = 0
        self.rollback_count: int = 0
        self._add_count = 0

        self._identities = FakeIdentityRepository()
        self._profiles = FakeProfileRepository()
        self._sessions = FakeSessionRepository()
        self._user_search = FakeUserSearchReader()

    @property
    def identities(self) -> FakeIdentityRepository:
        return self._identities

    @property
    def profiles(self) -> FakeProfileRepository:
        return self._profiles

    @property
    def sessions(self) -> FakeSessionRepository:
        return self._sessions

    @property
    def user_search(self) -> FakeUserSearchReader:
        return self._user_search

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1

    async def __aenter__(self) -> FakeUsersUnitOfWork:
        self._add_count = len(self._identities.added)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc is None:
            await self.commit()
        else:
            await self.rollback()
            self._identities.rollback_to(self._add_count)
