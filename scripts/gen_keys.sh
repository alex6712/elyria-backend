#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
KEYS_DIR="$PROJECT_ROOT/keys"
ENV_FILE="$PROJECT_ROOT/.env"
PRIVATE_KEY="$KEYS_DIR/private_key.pem"
PUBLIC_KEY="$KEYS_DIR/public_key.pem"

# Число итераций PBKDF2 при шифровании приватного ключа (OpenSSL по умолчанию: 2048).
KDF_ITERATIONS=600000

FORCE=false

usage() {
    echo "Usage: $(basename "$0") [-f|--force] [-h|--help]"
    echo "  -f, --force   overwrite existing keys"
}

die() {
    echo "Error: $*" >&2
    exit 1
}

# Читает значение переменной из .env без source (чтобы не выполнять код из файла).
# Снимает CR от CRLF и одну пару внешних кавычек, остальное не трогает.
get_env_value() {
    local name="$1" file="$2" line value

    line="$(grep -m1 -E "^(export[[:space:]]+)?${name}=" "$file" || true)"
    value="${line#*=}"
    value="${value%$'\r'}"

    case "$value" in
        \"*\") value="${value#\"}"; value="${value%\"}" ;;
        \'*\') value="${value#\'}"; value="${value%\'}" ;;
    esac

    printf '%s' "$value"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

command -v openssl >/dev/null 2>&1 || die "openssl is not installed"
[[ -f "$ENV_FILE" ]] || die "File .env not found"

password="$(get_env_value PRIVATE_SIGNATURE_KEY_PASSWORD "$ENV_FILE")"
[[ -n "$password" ]] || die "There's no PRIVATE_SIGNATURE_KEY_PASSWORD variable in .env"

if [[ -e "$PRIVATE_KEY" || -e "$PUBLIC_KEY" ]]; then
    if [[ "$FORCE" = false ]]; then
        if [[ -e "$PRIVATE_KEY" && -e "$PUBLIC_KEY" ]]; then
            echo "Keys already exist. Use -f/--force to overwrite."
            exit 0
        fi
        die "Only one key of the pair exists in $KEYS_DIR. Use -f/--force to regenerate the pair."
    fi
    echo "Force flag set - overwriting existing keys..."
fi

# Всё, что создаётся ниже, доступно только владельцу.
umask 077
mkdir -p -- "$KEYS_DIR"

# Ключи генерируются во временном каталоге и переносятся на место только после успеха,
# поэтому при сбое существующая пара не повреждается.
TMP_DIR="$(mktemp -d "$KEYS_DIR/.tmp.XXXXXX")"
trap 'rm -rf -- "$TMP_DIR"' EXIT INT

echo "Generating encrypted private key..."

# Пароль передаётся через окружение одной команды, а не через argv:
# так он не виден в списке процессов. Незашифрованный ключ идёт по pipe
# и на диск не попадает.
if ! openssl genpkey -algorithm Ed25519 \
    | SIGNATURE_KEY_PASSWORD="$password" openssl pkcs8 \
        -topk8 \
        -v2 aes-256-cbc \
        -iter "$KDF_ITERATIONS" \
        -passout env:SIGNATURE_KEY_PASSWORD \
        -out "$TMP_DIR/private_key.pem"; then
    die "Error while generating encrypted private signature key"
fi

echo "Generating public key..."

# Заодно проверяет, что приватный ключ расшифровывается заданным паролем.
if ! SIGNATURE_KEY_PASSWORD="$password" openssl pkey \
    -passin env:SIGNATURE_KEY_PASSWORD \
    -in "$TMP_DIR/private_key.pem" \
    -pubout \
    -out "$TMP_DIR/public_key.pem"; then
    die "Error while generating public signature key"
fi

chmod 600 "$TMP_DIR/private_key.pem"
chmod 644 "$TMP_DIR/public_key.pem"

mv -f -- "$TMP_DIR/private_key.pem" "$PRIVATE_KEY"
mv -f -- "$TMP_DIR/public_key.pem" "$PUBLIC_KEY"

echo "Generated private key: $PRIVATE_KEY"
echo "Generated public key: $PUBLIC_KEY"
echo "Ed25519 signature keys generated successfully!"
