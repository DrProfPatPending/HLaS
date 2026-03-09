#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_CONFIG_FILE="$BACKEND_DIR/server.config.json"
FRONTEND_CONFIG_FILE="$FRONTEND_DIR/server.config.json"

if [[ -x "$SCRIPT_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
elif [[ -x "$SCRIPT_DIR/../.venv/bin/python" ]]; then
    PYTHON_BIN="$SCRIPT_DIR/../.venv/bin/python"
else
    PYTHON_BIN="python3"
fi

read_config_defaults() {
    "$PYTHON_BIN" - "$BACKEND_CONFIG_FILE" "$FRONTEND_CONFIG_FILE" <<'PY'
import json
import os
import sys

backend_file = sys.argv[1]
frontend_file = sys.argv[2]

backend_default = {
    "server": {"host": "127.0.0.1", "port": 5050, "url": "http://127.0.0.1:5050"},
    "startup": {"delayMs": 3000},
    "runtime": {"debug": False, "useReloader": False},
}
frontend_default = {
    "server": {"host": "127.0.0.1", "port": 8080, "url": "http://127.0.0.1:8080"},
    "api": {"backendUrl": "http://127.0.0.1:5050"},
    "startup": {"delayMs": 3000},
}

def load(path, fallback):
    if not os.path.exists(path):
        return fallback
    try:
        with open(path, "r", encoding="utf-8") as handle:
            parsed = json.load(handle)
    except Exception:
        return fallback
    merged = dict(fallback)
    merged.update(parsed)
    for key in ("server", "startup", "runtime", "api"):
        if key in fallback:
            nested = dict(fallback.get(key, {}))
            nested.update(parsed.get(key, {}))
            merged[key] = nested
    return merged

backend = load(backend_file, backend_default)
frontend = load(frontend_file, frontend_default)

delay_ms = frontend["startup"]["delayMs"]
backend_host = backend["server"]["host"]
backend_port = backend["server"]["port"]
backend_url_base = backend["server"]["url"]
backend_debug = backend["runtime"].get("debug", False)
backend_reloader = backend["runtime"].get("useReloader", False)
frontend_host = frontend["server"]["host"]
frontend_port = frontend["server"]["port"]
frontend_url_base = frontend["server"]["url"]
frontend_backend_url = frontend["api"]["backendUrl"]

print(delay_ms)
print(backend_host)
print(backend_port)
print(backend_url_base)
print(str(backend_debug))
print(str(backend_reloader))
print(frontend_host)
print(frontend_port)
print(frontend_url_base)
print(frontend_backend_url)
PY
}

mapfile -t CONFIG_VALUES < <(read_config_defaults)

DEFAULT_DELAY_MS="${CONFIG_VALUES[0]}"
DEFAULT_BACKEND_HOST="${CONFIG_VALUES[1]}"
DEFAULT_BACKEND_PORT="${CONFIG_VALUES[2]}"
DEFAULT_BACKEND_URL_BASE="${CONFIG_VALUES[3]}"
DEFAULT_BACKEND_DEBUG="${CONFIG_VALUES[4]}"
DEFAULT_BACKEND_RELOADER="${CONFIG_VALUES[5]}"
DEFAULT_FRONTEND_HOST="${CONFIG_VALUES[6]}"
DEFAULT_FRONTEND_PORT="${CONFIG_VALUES[7]}"
DEFAULT_FRONTEND_URL_BASE="${CONFIG_VALUES[8]}"
DEFAULT_FRONTEND_BACKEND_URL="${CONFIG_VALUES[9]}"

DELAY_MS="${1:-${DELAY_MS:-$DEFAULT_DELAY_MS}}"
BIND_IP="${BIND_IP:-${DEFAULT_FRONTEND_HOST:-$DEFAULT_BACKEND_HOST}}"
BACKEND_PORT="${BACKEND_PORT:-$DEFAULT_BACKEND_PORT}"
FRONTEND_PORT="${FRONTEND_PORT:-$DEFAULT_FRONTEND_PORT}"
BACKEND_DEBUG="${BACKEND_DEBUG:-$DEFAULT_BACKEND_DEBUG}"
BACKEND_RELOADER="${BACKEND_RELOADER:-$DEFAULT_BACKEND_RELOADER}"

BACKEND_URL="${BACKEND_URL:-${DEFAULT_BACKEND_URL_BASE%/}/members}"
FRONTEND_URL="${FRONTEND_URL:-${DEFAULT_FRONTEND_URL_BASE%/}/}"
VUE_APP_BACKEND_URL="${VUE_APP_BACKEND_URL:-$DEFAULT_FRONTEND_BACKEND_URL}"

SLEEP_SECONDS=$(awk "BEGIN {printf \"%.3f\", $DELAY_MS / 1000}")

test_server_url() {
    local url="$1"
    curl --silent --show-error --max-time 5 "$url" >/dev/null 2>&1
}

(
    cd "$BACKEND_DIR" || exit 1
    nohup "$PYTHON_BIN" -c "import app; app.configure_logging(); app.app.run(host='${BIND_IP}', port=${BACKEND_PORT}, debug=${BACKEND_DEBUG}, use_reloader=${BACKEND_RELOADER})" >/dev/null 2>&1 &
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
    export VUE_APP_BACKEND_URL
    nohup npm run serve -- --host "$BIND_IP" --port "$FRONTEND_PORT" >/dev/null 2>&1 &
    echo $! > "$SCRIPT_DIR/.frontend.pid"
)

sleep "$SLEEP_SECONDS"

if test_server_url "$FRONTEND_URL"; then
    echo "Server Running"
else
    echo "Server Not Running"
    exit 1
fi
