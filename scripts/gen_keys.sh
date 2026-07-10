#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEYS_DIR="$PROJECT_ROOT/keys"
ENV_FILE="$PROJECT_ROOT/.env"
FORCE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -f|--force)
            FORCE=true
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: $(basename "$0") [-f|--force]"
            exit 1
            ;;
    esac
done

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: File .env not found"
    exit 1
fi

echo "Generating Ed25519 signature keys..."

mkdir -p "$KEYS_DIR"

PRIVATE_SIGNATURE_KEY_PASSWORD=$(
    grep -m1 '^PRIVATE_SIGNATURE_KEY_PASSWORD=' "$ENV_FILE" \
    | cut -d'=' -f2- \
    | tr -d '"'
)

if [ -z "$PRIVATE_SIGNATURE_KEY_PASSWORD" ]; then
    echo "Error: There's no PRIVATE_SIGNATURE_KEY_PASSWORD variable in .env"
    exit 1
fi

PRIVATE_KEY="$KEYS_DIR/private_key.pem"
PUBLIC_KEY="$KEYS_DIR/public_key.pem"

if [ -f "$PRIVATE_KEY" ] || [ -f "$PUBLIC_KEY" ]; then
    if [ "$FORCE" = false ]; then
        echo "Keys already exist. Use -f/--force to overwrite."
        exit 0
    fi
    echo "Force flag set - overwriting existing keys..."
fi

cd "$KEYS_DIR" || exit 1

echo "Generating encrypted private key..."

openssl genpkey \
    -algorithm Ed25519 \
    | openssl pkcs8 \
        -topk8 \
        -v2 aes-256-cbc \
        -passout pass:"$PRIVATE_SIGNATURE_KEY_PASSWORD" \
        -out $PRIVATE_KEY

if [ $? -ne 0 ]; then
    echo "Error while generating encrypted private signature key"
    exit 1
fi

echo "Generated private key: $PRIVATE_KEY"

echo "Generating public key..."

openssl pkey \
    -passin pass:"$PRIVATE_SIGNATURE_KEY_PASSWORD" \
    -in $PRIVATE_KEY \
    -pubout \
    -out $PUBLIC_KEY

if [ $? -ne 0 ]; then
    echo "Error while generating public signature key"
    exit 1
fi

echo "Generated public signature key: $PUBLIC_KEY"

echo "Ed25519 signature keys generated successfully!"
