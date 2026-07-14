#!/usr/bin/env sh
set -eu

MODE="${1:-sqlite}"
ROOT_DIR="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT_DIR/apps/api/.env"

if [ -e "$ENV_FILE" ]; then
  printf '%s\n' "Refusing to overwrite $ENV_FILE. Remove it first if you want a new local key."
  exit 1
fi

case "$MODE" in
  sqlite)
    DATABASE_URL="sqlite+aiosqlite:///./var/msme_saarthi_local.db"
    RETRIEVAL_PROVIDER="curated"
    mkdir -p "$ROOT_DIR/apps/api/var"
    ;;
  postgres)
    DATABASE_URL="postgresql+asyncpg://msme_saarthi:local-development-only@127.0.0.1:5432/msme_saarthi"
    RETRIEVAL_PROVIDER="opensearch"
    ;;
  *)
    printf '%s\n' "Usage: $0 [sqlite|postgres]" >&2
    exit 2
    ;;
esac

ENCRYPTION_KEY="$(openssl rand -base64 32)"
umask 077
{
  printf '%s\n' "MSME_SAARTHI_ENVIRONMENT=local"
  printf '%s\n' "MSME_SAARTHI_DEBUG=false"
  printf '%s\n' "MSME_SAARTHI_LOG_LEVEL=INFO"
  printf '%s\n' "MSME_SAARTHI_DATABASE_URL=$DATABASE_URL"
  printf '%s\n' "MSME_SAARTHI_DATA_ENCRYPTION_KEY=$ENCRYPTION_KEY"
  printf '%s\n' "MSME_SAARTHI_DATA_ENCRYPTION_KEY_VERSION=v1"
  printf '%s\n' "MSME_SAARTHI_WEB_ORIGIN=http://127.0.0.1:5173"
  printf '%s\n' "MSME_SAARTHI_SESSION_COOKIE_SECURE=false"
  printf '%s\n' "MSME_SAARTHI_RETRIEVAL_PROVIDER=$RETRIEVAL_PROVIDER"
  printf '%s\n' "MSME_SAARTHI_EMBEDDING_PROVIDER=local"
  printf '%s\n' "MSME_SAARTHI_EMBEDDING_MODEL=text-embedding-3-small"
  printf '%s\n' "MSME_SAARTHI_EMBEDDING_DIMENSIONS=384"
  printf '%s\n' "MSME_SAARTHI_OPENSEARCH_URL=http://127.0.0.1:9200"
  printf '%s\n' "MSME_SAARTHI_OPENSEARCH_INDEX=msme-schemes-v2"
  printf '%s\n' "MSME_SAARTHI_LLM_PROVIDER=mock"
  printf '%s\n' "MSME_SAARTHI_OPENAI_MODEL=gpt-5.4-mini"
} > "$ENV_FILE"

printf '%s\n' "Created $ENV_FILE for $MODE development with permissions restricted by umask 077."
