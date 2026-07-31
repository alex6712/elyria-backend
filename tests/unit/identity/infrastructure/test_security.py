"""Unit-тесты сервисов безопасности: JWT, HMAC, Argon2id, ключи."""

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from cryptography.hazmat.primitives.asymmetric.rsa import (
    generate_private_key,
)

from src.identity.application.dto import TokenClaimsDTO
from src.identity.application.exceptions import (
    TokenExpiredError,
    TokenInvalidError,
    TokenSignatureInvalidError,
)
from src.identity.infrastructure.security import (
    Argon2idPasswordHasher,
    HmacSha256TokenHasher,
    JwtTokenIssuer,
    JwtTokenVerifier,
)
from src.identity.infrastructure.security.signature_keys_provider import (
    SignatureKeys,
)

ISSUER = "Elyria Backend"
ALGORITHM = "EdDSA"


class TestJwtTokenIssuer:
    """Проверка выпуска JWT-токенов."""

    @pytest.fixture
    def issuer(self, ed25519_key_pair: tuple) -> JwtTokenIssuer:
        """Эмитент токенов на тестовом ключе."""
        *_, private_key = ed25519_key_pair
        return JwtTokenIssuer(ISSUER, private_key, ALGORITHM)

    @pytest.fixture
    def claims(self) -> TokenClaimsDTO:
        """Утверждения токена для теста."""
        return TokenClaimsDTO(
            user_id="11111111-1111-1111-1111-111111111111",
            expires_at="2026-12-31T00:00:00Z",
            issued_at="2026-01-01T00:00:00Z",
            token_id="22222222-2222-2222-2222-222222222222",
            session_id="33333333-3333-3333-3333-333333333333",
        )

    def test_issue_produces_three_part_token(
        self, issuer: JwtTokenIssuer, claims: TokenClaimsDTO
    ) -> None:
        """Результат — компактный JWT из трёх частей."""
        token = issuer.issue(claims)

        assert len(token.split(".")) == 3

    def test_issue_embeds_all_claims(
        self,
        issuer: JwtTokenIssuer,
        claims: TokenClaimsDTO,
        ed25519_key_pair: tuple,
    ) -> None:
        """Все шесть утверждений корректно попадают в токен."""
        token = issuer.issue(claims)
        public_key_path, *_, _ = ed25519_key_pair
        public_key = serialization.load_pem_public_key(public_key_path.read_bytes())

        payload = jwt.decode(
            token,
            public_key,
            algorithms=[ALGORITHM],
            options={"verify_exp": False},
        )

        assert payload["iss"] == ISSUER
        assert payload["sub"] == str(claims.user_id)
        assert payload["exp"] == int(claims.expires_at.timestamp())
        assert payload["iat"] == int(claims.issued_at.timestamp())
        assert payload["jti"] == str(claims.token_id)
        assert payload["sid"] == str(claims.session_id)

    def test_issue_header(self, issuer: JwtTokenIssuer, claims: TokenClaimsDTO) -> None:
        """Заголовок токена содержит алгоритм EdDSA и тип JWT."""
        token = issuer.issue(claims)

        header = jwt.get_unverified_header(token)

        assert header["alg"] == "EdDSA"
        assert header["typ"] == "JWT"


class TestJwtTokenVerifier:
    """Проверка проверки JWT-токенов."""

    @pytest.fixture
    def key_pair(self, ed25519_key_pair: tuple) -> SignatureKeys:
        """Пара ключей Ed25519 для эмитента и верификатора."""
        public_key_path, _, _, private_key = ed25519_key_pair
        public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
        return SignatureKeys(public=public_key, private=private_key)

    @pytest.fixture
    def verifier(self, key_pair: SignatureKeys) -> JwtTokenVerifier:
        """Верификатор токенов на тестовом ключе."""
        return JwtTokenVerifier(ISSUER, key_pair.public, ALGORITHM)

    @pytest.fixture
    def issuer(self, key_pair: SignatureKeys) -> JwtTokenIssuer:
        """Эмитент токенов на тестовом ключе."""
        return JwtTokenIssuer(ISSUER, key_pair.private, ALGORITHM)

    def test_verify_round_trip(
        self,
        verifier: JwtTokenVerifier,
        issuer: JwtTokenIssuer,
    ) -> None:
        """Токен эмитента проходит проверку и возвращает те же claims."""
        claims = TokenClaimsDTO(
            user_id="11111111-1111-1111-1111-111111111111",
            expires_at="2026-12-31T00:00:00Z",
            issued_at="2026-01-01T00:00:00Z",
            token_id="22222222-2222-2222-2222-222222222222",
            session_id="33333333-3333-3333-3333-333333333333",
        )

        token = issuer.issue(claims)
        verified = verifier.verify(token)

        assert verified == claims

    def test_verify_expired_token_raises(self, key_pair: SignatureKeys) -> None:
        """Токен с истёкшим сроком отклоняется."""
        verifier = JwtTokenVerifier(ISSUER, key_pair.public, ALGORITHM)
        issuer = JwtTokenIssuer(ISSUER, key_pair.private, ALGORITHM)
        claims = TokenClaimsDTO(
            user_id="11111111-1111-1111-1111-111111111111",
            expires_at="2020-01-01T00:00:00Z",
            issued_at="2019-01-01T00:00:00Z",
            token_id="22222222-2222-2222-2222-222222222222",
            session_id="33333333-3333-3333-3333-333333333333",
        )

        with pytest.raises(TokenExpiredError):
            verifier.verify(issuer.issue(claims))

    def test_verify_foreign_signature_raises(
        self,
        verifier: JwtTokenVerifier,
    ) -> None:
        """Токен, подписанный другим ключом, отклоняется."""
        other_key = Ed25519PrivateKey.generate()
        foreign_issuer = JwtTokenIssuer(ISSUER, other_key, ALGORITHM)
        token = foreign_issuer.issue(
            TokenClaimsDTO(
                user_id="11111111-1111-1111-1111-111111111111",
                expires_at="2026-12-31T00:00:00Z",
                issued_at="2026-01-01T00:00:00Z",
                token_id="22222222-2222-2222-2222-222222222222",
                session_id="33333333-3333-3333-3333-333333333333",
            )
        )

        with pytest.raises(TokenSignatureInvalidError):
            verifier.verify(token)

    def test_verify_missing_claims_raises(
        self,
        verifier: JwtTokenVerifier,
        key_pair: SignatureKeys,
    ) -> None:
        """Токен без обязательного утверждения отклоняется."""
        token = jwt.encode(
            {"iss": ISSUER, "sub": "11111111-1111-1111-1111-111111111111"},
            key_pair.private,
            algorithm=ALGORITHM,
        )

        with pytest.raises(TokenInvalidError):
            verifier.verify(token)

    def test_verify_wrong_issuer_raises(
        self,
        verifier: JwtTokenVerifier,
        key_pair: SignatureKeys,
    ) -> None:
        """Токен с чужим издателем отклоняется."""
        token = jwt.encode(
            {
                "iss": "Other Service",
                "sub": "11111111-1111-1111-1111-111111111111",
                "exp": 2000000000,
                "iat": 1000000000,
                "jti": "22222222-2222-2222-2222-222222222222",
                "sid": "33333333-3333-3333-3333-333333333333",
            },
            key_pair.private,
            algorithm=ALGORITHM,
        )

        with pytest.raises(TokenInvalidError):
            verifier.verify(token)

    def test_verify_non_uuid_subject_raises(
        self,
        verifier: JwtTokenVerifier,
        key_pair: SignatureKeys,
    ) -> None:
        """Токен с некорректным идентификатором пользователя отклоняется."""
        token = jwt.encode(
            {
                "iss": ISSUER,
                "sub": "not-a-uuid",
                "exp": 2000000000,
                "iat": 1000000000,
                "jti": "22222222-2222-2222-2222-222222222222",
                "sid": "33333333-3333-3333-3333-333333333333",
            },
            key_pair.private,
            algorithm=ALGORITHM,
        )

        with pytest.raises(TokenInvalidError):
            verifier.verify(token)

    def test_verify_future_nbf_raises(
        self,
        verifier: JwtTokenVerifier,
        key_pair: SignatureKeys,
    ) -> None:
        """Токен, не вступивший в силу (nbf в будущем), отклоняется."""
        token = jwt.encode(
            {
                "iss": ISSUER,
                "sub": "11111111-1111-1111-1111-111111111111",
                "exp": 2000000000,
                "iat": 1000000000,
                "nbf": 3000000000,
                "jti": "22222222-2222-2222-2222-222222222222",
                "sid": "33333333-3333-3333-3333-333333333333",
            },
            key_pair.private,
            algorithm=ALGORITHM,
        )

        with pytest.raises(TokenInvalidError):
            verifier.verify(token)

    def test_verify_garbage_raises(self, verifier: JwtTokenVerifier) -> None:
        """Мусорная строка отклоняется как невалидный токен."""
        with pytest.raises(TokenInvalidError):
            verifier.verify("not.a.jwt")


class TestHmacSha256TokenHasher:
    """Проверка HMAC-SHA256 хеширования токенов."""

    def test_deterministic(self) -> None:
        """Одинаковый вход даёт одинаковый хеш."""
        hasher = HmacSha256TokenHasher(b"secret")

        assert hasher.hash("token-a") == hasher.hash("token-a")

    def test_sensitive_to_secret(self) -> None:
        """Разный секрет даёт разные хеши."""
        first = HmacSha256TokenHasher(b"secret-a")
        second = HmacSha256TokenHasher(b"secret-b")

        assert first.hash("token") != second.hash("token")

    def test_sensitive_to_input(self) -> None:
        """Разный вход даёт разные хеши."""
        hasher = HmacSha256TokenHasher(b"secret")

        assert hasher.hash("token-a") != hasher.hash("token-b")

    def test_hex_length(self) -> None:
        """Хеш — 64 шестнадцатеричных символа (SHA-256)."""
        hasher = HmacSha256TokenHasher(b"secret")

        result = hasher.hash("token")

        assert len(result) == 64

    def test_matches_hmac_reference(self) -> None:
        """Результат совпадает с эталонным вычислением HMAC."""
        import hashlib
        import hmac

        hasher = HmacSha256TokenHasher(b"secret")
        expected = hmac.new(b"secret", b"token", hashlib.sha256).hexdigest()

        assert hasher.hash("token") == expected


class TestArgon2idPasswordHasher:
    """Проверка Argon2id хеширования паролей."""

    def test_hash_verify_round_trip(self) -> None:
        """Пароль проходит проверку после хеширования."""
        hasher = Argon2idPasswordHasher()

        password_hash = hasher.hash("secureP@ss1!")

        assert hasher.verify("secureP@ss1!", password_hash) is True

    def test_wrong_password_rejected(self) -> None:
        """Неверный пароль не проходит проверку."""
        hasher = Argon2idPasswordHasher()
        password_hash = hasher.hash("secureP@ss1!")

        assert hasher.verify("wrong_password", password_hash) is False

    def test_hash_prefix(self) -> None:
        """Хеш начинается с маркера алгоритма Argon2id."""
        hasher = Argon2idPasswordHasher()

        assert hasher.hash("secureP@ss1!").startswith("$argon2id$")

    def test_salt_is_random(self) -> None:
        """Разные хеши одного пароля (случайная соль)."""
        hasher = Argon2idPasswordHasher()

        assert hasher.hash("secureP@ss1!") != hasher.hash("secureP@ss1!")

    def test_verify_and_update_fresh_hash(self) -> None:
        """Свежий хеш не требует обновления."""
        hasher = Argon2idPasswordHasher()
        password_hash = hasher.hash("secureP@ss1!")

        matches, new_hash = hasher.verify_and_update("secureP@ss1!", password_hash)

        assert matches is True
        assert new_hash is None


class TestSignatureKeysProvider:
    """Проверка провайдера ключей подписи."""

    def test_loads_ed25519_keys(
        self, ed25519_key_pair: tuple, make_signature_keys_provider
    ) -> None:
        """Загружается корректная пара ключей Ed25519."""
        public_path, private_path, password, _ = ed25519_key_pair
        provider = make_signature_keys_provider(
            public_key_path=public_path,
            private_key_path=private_path,
            password=password,
        )

        keys = provider.get_signature_keys()

        assert isinstance(
            keys.public,
            type(serialization.load_pem_public_key(public_path.read_bytes())),
        )
        assert isinstance(keys.private, Ed25519PrivateKey)

    def test_wrong_password_raises(
        self, ed25519_key_pair: tuple, make_signature_keys_provider
    ) -> None:
        """Неверный пароль расшифровки отклоняется с ValueError."""
        public_path, private_path, _, _ = ed25519_key_pair
        provider = make_signature_keys_provider(
            public_key_path=public_path,
            private_key_path=private_path,
            password="wrong-password",
        )

        with pytest.raises(ValueError, match="Failed to decrypt private key"):
            provider.get_signature_keys()

    def test_missing_file_raises(self, tmp_path, make_signature_keys_provider) -> None:
        """Отсутствующий файл ключа пробрасывает FileNotFoundError."""
        provider = make_signature_keys_provider(
            public_key_path=tmp_path / "missing.pem",
            private_key_path=tmp_path / "missing.pem",
            password="password",
        )

        with pytest.raises(FileNotFoundError):
            provider.get_signature_keys()

    def test_rsa_public_key_rejected(
        self, tmp_path, make_signature_keys_provider
    ) -> None:
        """Публичный ключ не-Ed25519 отклоняется с ValueError."""
        rsa_key = generate_private_key(public_exponent=65537, key_size=2048)
        rsa_public_pem = rsa_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        public_path = tmp_path / "rsa_public.pem"
        private_path = tmp_path / "rsa_private.pem"
        public_path.write_bytes(rsa_public_pem)

        private_pem = rsa_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        private_path.write_bytes(private_pem)

        provider = make_signature_keys_provider(
            public_key_path=public_path,
            private_key_path=private_path,
            password="irrelevant",
        )

        with pytest.raises(ValueError, match="Expected Ed25519 public key"):
            provider.get_signature_keys()

    def test_cache_after_first_load(
        self,
        ed25519_key_pair: tuple,
        make_signature_keys_provider,
    ) -> None:
        """Ключи кэшируются: последующая загрузка не обращается к файлам."""
        public_path, private_path, password, _ = ed25519_key_pair
        provider = make_signature_keys_provider(
            public_key_path=public_path,
            private_key_path=private_path,
            password=password,
        )

        first = provider.get_signature_keys()

        public_path.unlink()
        private_path.unlink()

        second = provider.get_signature_keys()

        assert first == second
