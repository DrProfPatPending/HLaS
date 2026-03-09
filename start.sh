#!/usr/bin/env bash
set -u

DELAY_MS="${1:-3000}"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:5000/members}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:8080/}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

if [[ -x "$SCRIPT_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
else
    PYTHON_BIN="python3"
fi

SLEEP_SECONDS=$(awk "BEGIN {printf \"%.3f\", $DELAY_MS / 1000}")

test_server_url() {
    local url="$1"
    curl --silent --fail --show-error --max-time 5 "$url" >/dev/null 2>&1
}

(
    cd "$BACKEND_DIR" || exit 1
    nohup "$PYTHON_BIN" app.py >/dev/null 2>&1 &
    echo $! > "$SCRIPT_DIR/.backend.pid"
)

sleep "$SLEEP_SECONDS"

if test_server_url "$BACKEND_URL"; then
    echo "Backend Running"
else
    echo "Server Not Running"
    if [[ -f "$SCRIPT_DIR/.backend.pid" ]]; then
        BACKEND_PID="$(cat "$SCRIPT_DIR/.backend.pid")"
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            kill "$BACKEND_PID" 2>/dev/null || true
        fi
    fi
    exit 1
fi

(
    cd "$FRONTEND_DIR" || exit 1
    nohup npm run serve >/dev/null 2>&1 &
    echo $! > "$SCRIPT_DIR/.frontend.pid"
)

sleep "$SLEEP_SECONDS"

if test_server_url "$FRONTEND_URL"; then
    echo "Server Running"
else
    echo "Server Not Running"
    exit 1
fi
