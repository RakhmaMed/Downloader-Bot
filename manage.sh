#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${LOG_DIR:-$APP_DIR/logs}"
PID_FILE="${PID_FILE:-$APP_DIR/.bot.pid}"
ENV_FILE="${ENV_FILE:-$APP_DIR/.env}"

load_env() {
  if [ -f "$ENV_FILE" ]; then
    set -o allexport
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +o allexport
  fi
}

ensure_uv() {
  if ! command -v uv >/dev/null 2>&1; then
    python3 -m pip install --upgrade pip >/dev/null
    python3 -m pip install --upgrade uv
  fi
}

install_deps() {
  ensure_uv
  cd "$APP_DIR"

  if [ -f "$APP_DIR/uv.lock" ]; then
    uv sync --frozen --locked || uv sync
  else
    uv sync
  fi
}

run_polling() {
  load_env
  cd "$APP_DIR"
  BOT_MODE=polling uv run main.py "$@"
}

run_webhook() {
  load_env
  cd "$APP_DIR"

  if [ -z "${WEBHOOK_HOST:-}" ]; then
    echo "WEBHOOK_HOST is required for webhook mode (public https URL behind nginx)"
    exit 1
  fi

  BOT_MODE=webhook uv run main.py "$@"
}

deploy() {
  load_env
  install_deps
  mkdir -p "$LOG_DIR"

  stop || true

  local mode
  mode="${BOT_MODE:-webhook}"

  if [ "$mode" = "webhook" ] && [ -z "${WEBHOOK_HOST:-}" ]; then
    echo "WEBHOOK_HOST is required for webhook deploy"
    exit 1
  fi

  cd "$APP_DIR"
  nohup env BOT_MODE="$mode" uv run main.py >"$LOG_DIR/bot.log" 2>&1 &
  echo $! >"$PID_FILE"
  echo "Bot started in $mode mode (pid $(cat "$PID_FILE")). Logs: $LOG_DIR/bot.log"
}

stop() {
  if [ -f "$PID_FILE" ]; then
    local pid
    pid=$(cat "$PID_FILE")
    if ps -p "$pid" >/dev/null 2>&1; then
      kill "$pid"
      echo "Stopped process $pid"
    else
      echo "Process $pid not running"
    fi
    rm -f "$PID_FILE"
  else
    return 1
  fi
}

status() {
  if [ -f "$PID_FILE" ]; then
    local pid
    pid=$(cat "$PID_FILE")
    if ps -p "$pid" >/dev/null 2>&1; then
      echo "Bot is running (pid $pid)"
      return 0
    fi
  fi
  echo "Bot is not running"
  return 1
}

usage() {
  cat <<'EOF'
Usage: ./manage.sh <command>
  install        Install dependencies with uv
  run-polling    Run the bot in polling mode (foreground)
  run-webhook    Run the bot in webhook mode (foreground)
  deploy         Install deps and start in background (uses BOT_MODE or webhook)
  stop           Stop background process started by deploy
  status         Show process status
  help           Show this message
Env:
  ENV_FILE (default: ./.env), LOG_DIR, PID_FILE, BOT_MODE
EOF
}

cmd="${1:-help}"
shift || true

case "$cmd" in
  install) install_deps "$@" ;;
  run-polling) run_polling "$@" ;;
  run-webhook) run_webhook "$@" ;;
  deploy) deploy "$@" ;;
  stop) stop "$@" ;;
  status) status "$@" ;;
  help|--help|-h) usage ;;
  *) echo "Unknown command: $cmd"; usage; exit 1 ;;
esac

