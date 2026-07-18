#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
STATE_DIR="$ROOT_DIR/.local/run"
LOG_DIR="$ROOT_DIR/.local/log"
API_PID_FILE="$STATE_DIR/api.pid"
WEB_PID_FILE="$STATE_DIR/web.pid"
API_LOG="$LOG_DIR/api.log"
WEB_LOG="$LOG_DIR/web.log"
COMPOSE_FILE="$ROOT_DIR/infrastructure/compose.yaml"
PYTHON="${PYTHON:-$ROOT_DIR/.venv/bin/python}"
API_URL="${API_URL:-http://127.0.0.1:8000}"
WEB_URL="${WEB_URL:-http://127.0.0.1:5173}"

mkdir -p "$STATE_DIR" "$LOG_DIR"

usage() {
  printf '%s\n' "Usage: $0 {start|stop|restart|status|logs [--follow]}" >&2
  exit 2
}

pid_is_running() {
  pid_file="$1"
  [ -f "$pid_file" ] || return 1
  pid="$(cat "$pid_file")"
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

remove_stale_pid() {
  pid_file="$1"
  if [ -f "$pid_file" ] && ! pid_is_running "$pid_file"; then
    rm -f "$pid_file"
  fi
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'Missing required command: %s\n' "$1" >&2
    exit 1
  }
}

wait_for_url() {
  label="$1"
  url="$2"
  attempts="${3:-60}"
  count=0
  while [ "$count" -lt "$attempts" ]; do
    if curl --fail --silent --show-error "$url" >/dev/null 2>&1; then
      printf '%s is ready: %s\n' "$label" "$url"
      return 0
    fi
    count=$((count + 1))
    sleep 1
  done
  printf '%s did not become ready: %s\n' "$label" "$url" >&2
  return 1
}

start_processes() {
  remove_stale_pid "$API_PID_FILE"
  remove_stale_pid "$WEB_PID_FILE"

  if ! pid_is_running "$API_PID_FILE"; then
    : > "$API_LOG"
    "$PYTHON" "$ROOT_DIR/scripts/run-detached.py" \
      --cwd "$ROOT_DIR/apps/api" \
      --log "$API_LOG" \
      --pid-file "$API_PID_FILE" \
      -- "$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
    printf 'Started API (PID %s).\n' "$(cat "$API_PID_FILE")"
  else
    printf 'API is already running (PID %s).\n' "$(cat "$API_PID_FILE")"
  fi

  if ! pid_is_running "$WEB_PID_FILE"; then
    : > "$WEB_LOG"
    "$PYTHON" "$ROOT_DIR/scripts/run-detached.py" \
      --cwd "$ROOT_DIR/apps/web" \
      --log "$WEB_LOG" \
      --pid-file "$WEB_PID_FILE" \
      -- ./node_modules/.bin/vite --host 127.0.0.1 --port 5173 --strictPort
    printf 'Started web (PID %s).\n' "$(cat "$WEB_PID_FILE")"
  else
    printf 'Web is already running (PID %s).\n' "$(cat "$WEB_PID_FILE")"
  fi
}

start_all() {
  require_command docker
  require_command curl
  [ -x "$PYTHON" ] || {
    printf 'Python environment not found at %s. Run the install steps in docs/QUICKSTART.md.\n' "$PYTHON" >&2
    exit 1
  }
  [ -f "$ROOT_DIR/apps/api/.env" ] || {
    printf '%s\n' "Missing apps/api/.env. Run ./scripts/bootstrap-local.sh postgres first." >&2
    exit 1
  }
  [ -x "$ROOT_DIR/apps/web/node_modules/.bin/vite" ] || {
    printf '%s\n' "Web dependencies are missing. Run make web-install first." >&2
    exit 1
  }

  printf '%s\n' "Starting PostgreSQL, Redis and OpenSearch..."
  docker compose -f "$COMPOSE_FILE" up -d --wait

  printf '%s\n' "Applying database migrations..."
  (
    cd "$ROOT_DIR/apps/api"
    "$PYTHON" -m alembic upgrade head
  )

  start_processes
  if ! wait_for_url "API" "$API_URL/api/v1/health/live" 60; then
    tail -n 40 "$API_LOG" >&2 || true
    stop_process "$API_PID_FILE" "API"
    stop_process "$WEB_PID_FILE" "web"
    exit 1
  fi
  if ! wait_for_url "Web" "$WEB_URL" 60; then
    tail -n 40 "$WEB_LOG" >&2 || true
    stop_process "$API_PID_FILE" "API"
    stop_process "$WEB_PID_FILE" "web"
    exit 1
  fi

  printf '\nApplication: %s\nAPI docs:   %s/docs\nLogs:       make logs\nStop:       make stop\n' "$WEB_URL" "$API_URL"
}

stop_process() {
  pid_file="$1"
  label="$2"
  if ! pid_is_running "$pid_file"; then
    rm -f "$pid_file"
    printf '%s is not running.\n' "$label"
    return
  fi

  pid="$(cat "$pid_file")"
  kill "$pid" 2>/dev/null || true
  count=0
  while kill -0 "$pid" 2>/dev/null && [ "$count" -lt 10 ]; do
    count=$((count + 1))
    sleep 1
  done
  if kill -0 "$pid" 2>/dev/null; then
    printf '%s did not stop cleanly; sending SIGKILL.\n' "$label" >&2
    kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$pid_file"
  printf 'Stopped %s.\n' "$label"
}

stop_all() {
  stop_process "$WEB_PID_FILE" "web"
  stop_process "$API_PID_FILE" "API"
  if command -v docker >/dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" down
  fi
}

show_status() {
  exit_code=0
  for entry in "API:$API_PID_FILE:$API_URL/api/v1/health/live" "Web:$WEB_PID_FILE:$WEB_URL"; do
    label="${entry%%:*}"
    remainder="${entry#*:}"
    pid_file="${remainder%%:*}"
    url="${remainder#*:}"
    if pid_is_running "$pid_file"; then
      if curl --fail --silent "$url" >/dev/null 2>&1; then
        printf '%-12s running  PID %-8s %s\n' "$label" "$(cat "$pid_file")" "$url"
      else
        printf '%-12s starting PID %-8s %s\n' "$label" "$(cat "$pid_file")" "$url"
        exit_code=1
      fi
    else
      printf '%-12s stopped\n' "$label"
      exit_code=1
    fi
  done
  if command -v docker >/dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" ps
  fi
  return "$exit_code"
}

show_logs() {
  if [ "${1:-}" = "--follow" ]; then
    touch "$API_LOG" "$WEB_LOG"
    exec tail -n 80 -f "$API_LOG" "$WEB_LOG"
  fi
  printf '%s\n' "==> API <=="
  tail -n 80 "$API_LOG" 2>/dev/null || printf '%s\n' "No API log yet."
  printf '%s\n' "==> Web <=="
  tail -n 80 "$WEB_LOG" 2>/dev/null || printf '%s\n' "No web log yet."
}

case "${1:-}" in
  start) start_all ;;
  stop) stop_all ;;
  restart) stop_all; start_all ;;
  status) show_status ;;
  logs) show_logs "${2:-}" ;;
  *) usage ;;
esac
