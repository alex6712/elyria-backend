"""Unit-тесты :class:`RefreshSessionUseCase`."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from src.identity.application.commands import RefreshSessionCommand
from src.identity.application.exceptions import (
    SessionNotFoundError,
    TokenExpiredError,
    TokenInvalidError,
    TokenSignatureInvalidError,
)
from src.identity.application.use_cases import RefreshSessionUseCase
from src.identity.domain.entities import Session
from src.identity.domain.exceptions import SessionInvalidError
from src.shared.domain.exceptions import ConcurrentModificationError
from tests.fakes.identity_uow import (
    FakeIdentityUnitOfWork,
    FakeSessionRepository,
)
from tests.fakes.security import FakeTokenHasher, FakeTokenIssuer, FakeTokenVerifier
from tests.unit.identity.application.conftest import make_claims

REFRESH_TOKEN = "refresh-token-value"
SESSION_SECRET = f"hashed:{REFRESH_TOKEN}"


def build_use_case(
    *,
    uow: FakeIdentityUnitOfWork,
    token_issuer: FakeTokenIssuer,
    token_verifier: FakeTokenVerifier,
    token_hasher: FakeTokenHasher,
    at_lifetime_minutes: int,
    rt_lifetime_days: int,
) -> RefreshSessionUseCase:
    """Собрать use case обновления сессии из фейков."""
    return RefreshSessionUseCase(
        uow=uow,
        token_issuer=token_issuer,
        token_verifier=token_verifier,
        token_hasher=token_hasher,
        at_lifetime_minutes=at_lifetime_minutes,
        rt_lifetime_days=rt_lifetime_days,
    )


def make_valid_session(
    *,
    identity_id: UUID | None = None,
    session_secret: str = SESSION_SECRET,
) -> tuple[Session, FakeTokenVerifier]:
    """Создать валидную сессию и верификатор для её refresh-токена."""
    session_id = uuid4()
    resolved_identity_id = identity_id or uuid4()
    session = Session.issue(
        id=session_id,
        identity_id=resolved_identity_id,
        session_secret=session_secret,
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    verifier = FakeTokenVerifier(
        claims=make_claims(
            user_id=resolved_identity_id,
            session_id=session_id,
            token_id=uuid4(),
        )
    )
    return session, verifier


class TestRefreshSessionUseCaseSuccess:
    """Сценарии успешного обновления сессии."""

    async def test_rotates_secret_and_returns_new_pair(
        self,
        uow: FakeIdentityUnitOfWork,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Секрет ротируется, session_id сохраняется, выдаётся новая пара."""
        session, verifier = make_valid_session()
        await uow.session_repo.add(session)

        before = datetime.now(UTC)
        use_case = build_use_case(
            uow=uow,
            token_issuer=token_issuer,
            token_verifier=verifier,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )
        result = await use_case.execute(
            RefreshSessionCommand(refresh_token=REFRESH_TOKEN)
        )
        after = datetime.now(UTC)

        stored = await uow.session_repo.get_by_id(session.id)
        assert stored is not None
        assert stored.session_secret == token_hasher.hash(result.refresh_token)
        assert stored.session_secret != SESSION_SECRET
        assert stored.expires_at == stored.updated_at + timedelta(days=rt_lifetime_days)

        new_refresh_claims = token_issuer.issued[0]
        new_access_claims = token_issuer.issued[1]
        assert new_refresh_claims.session_id == session.id
        assert new_access_claims.session_id == session.id
        assert new_refresh_claims.user_id == session.identity_id
        assert before <= new_refresh_claims.issued_at <= after
        assert (
            new_refresh_claims.expires_at
            == new_refresh_claims.issued_at + timedelta(days=rt_lifetime_days)
        )
        assert new_access_claims.expires_at == new_access_claims.issued_at + timedelta(
            minutes=at_lifetime_minutes
        )

    async def test_old_refresh_token_rejected_after_rotation(
        self,
        uow: FakeIdentityUnitOfWork,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Повторное использование старого refresh-токена отклоняется."""
        session, verifier = make_valid_session()
        await uow.session_repo.add(session)

        use_case = build_use_case(
            uow=uow,
            token_issuer=token_issuer,
            token_verifier=verifier,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )
        await use_case.execute(RefreshSessionCommand(refresh_token=REFRESH_TOKEN))

        with pytest.raises(SessionNotFoundError):
            await use_case.execute(RefreshSessionCommand(refresh_token=REFRESH_TOKEN))

        assert len(uow.session_repo.rotation_calls) == 1

    async def test_commits_unit_of_work(
        self,
        uow: FakeIdentityUnitOfWork,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Успешное обновление фиксирует транзакцию."""
        session, verifier = make_valid_session()
        await uow.session_repo.add(session)

        use_case = build_use_case(
            uow=uow,
            token_issuer=token_issuer,
            token_verifier=verifier,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )
        await use_case.execute(RefreshSessionCommand(refresh_token=REFRESH_TOKEN))

        assert uow.commit_count == 1
        assert uow.rollback_count == 0


class TestRefreshSessionUseCaseFailures:
    """Сценарии неуспешного обновления сессии."""

    async def test_missing_session_raises_not_found(
        self,
        uow: FakeIdentityUnitOfWork,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Сессия из claims отсутствует в хранилище."""
        _, verifier = make_valid_session()

        use_case = build_use_case(
            uow=uow,
            token_issuer=token_issuer,
            token_verifier=verifier,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        with pytest.raises(SessionNotFoundError) as exc_info:
            await use_case.execute(RefreshSessionCommand(refresh_token=REFRESH_TOKEN))

        assert "not found" in str(exc_info.value)
        assert uow.session_repo.rotation_calls == []
        assert uow.rollback_count == 1

    async def test_secret_mismatch_masked_as_not_found(
        self,
        uow: FakeIdentityUnitOfWork,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Чужой/старый токен маскируется под «сессия не найдена»."""
        session, verifier = make_valid_session(session_secret="hashed:other-token")
        await uow.session_repo.add(session)

        use_case = build_use_case(
            uow=uow,
            token_issuer=token_issuer,
            token_verifier=verifier,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        with pytest.raises(SessionNotFoundError):
            await use_case.execute(RefreshSessionCommand(refresh_token=REFRESH_TOKEN))

        assert uow.session_repo.rotation_calls == []

    async def test_revoked_session_raises_domain_error(
        self,
        uow: FakeIdentityUnitOfWork,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Отозванная сессия приводит к доменному SessionInvalidError.

        TODO(identity): docstring use case обещает ``SessionNotFoundError``
        для отозванной/истёкшей сессии, фактически пробрасывается доменный
        ``SessionInvalidError`` из ``rotate_secret``. Требуется решение
        разработчика: исправить docstring или обернуть исключение.
        """
        session, verifier = make_valid_session()
        session.revoke()
        await uow.session_repo.add(session)

        use_case = build_use_case(
            uow=uow,
            token_issuer=token_issuer,
            token_verifier=verifier,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        with pytest.raises(SessionInvalidError):
            await use_case.execute(RefreshSessionCommand(refresh_token=REFRESH_TOKEN))

        assert uow.session_repo.rotation_calls == []

    async def test_expired_session_raises_domain_error(
        self,
        uow: FakeIdentityUnitOfWork,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Истёкшая сессия приводит к доменному SessionInvalidError."""
        session_id = uuid4()
        session = Session.issue(
            id=session_id,
            identity_id=uuid4(),
            session_secret=SESSION_SECRET,
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        verifier = FakeTokenVerifier(
            claims=make_claims(
                user_id=session.identity_id,
                session_id=session_id,
                token_id=uuid4(),
            )
        )
        await uow.session_repo.add(session)

        use_case = build_use_case(
            uow=uow,
            token_issuer=token_issuer,
            token_verifier=verifier,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        with pytest.raises(SessionInvalidError):
            await use_case.execute(RefreshSessionCommand(refresh_token=REFRESH_TOKEN))

    @pytest.mark.parametrize(
        ("error", "expected"),
        [
            (TokenExpiredError("expired"), TokenExpiredError),
            (TokenSignatureInvalidError("bad signature"), TokenSignatureInvalidError),
            (TokenInvalidError("bad token"), TokenInvalidError),
        ],
    )
    async def test_verifier_errors_propagate(
        self,
        error: Exception,
        expected: type[Exception],
        uow: FakeIdentityUnitOfWork,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Ошибки верификатора пробрасываются, транзакция откатывается."""
        verifier = FakeTokenVerifier(error=error)
        use_case = build_use_case(
            uow=uow,
            token_issuer=token_issuer,
            token_verifier=verifier,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        with pytest.raises(expected):
            await use_case.execute(RefreshSessionCommand(refresh_token=REFRESH_TOKEN))

        assert token_issuer.issued == []
        assert uow.rollback_count == 1

    async def test_concurrent_modification_propagates(
        self,
        token_issuer: FakeTokenIssuer,
        token_hasher: FakeTokenHasher,
        at_lifetime_minutes: int,
        rt_lifetime_days: int,
    ) -> None:
        """Конфликт версии при сохранении ротации пробрасывается наружу."""
        sessions = FakeSessionRepository()
        session, verifier = make_valid_session()
        await sessions.add(session)
        sessions.fail_on_save_rotation = ConcurrentModificationError(
            session.id, "Session"
        )

        uow = FakeIdentityUnitOfWork(sessions=sessions)
        use_case = build_use_case(
            uow=uow,
            token_issuer=token_issuer,
            token_verifier=verifier,
            token_hasher=token_hasher,
            at_lifetime_minutes=at_lifetime_minutes,
            rt_lifetime_days=rt_lifetime_days,
        )

        with pytest.raises(ConcurrentModificationError):
            await use_case.execute(RefreshSessionCommand(refresh_token=REFRESH_TOKEN))

        assert uow.rollback_count == 1
