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
    "tls": {"enabled": False, "adhoc": True, "certFile": "", "keyFile": ""},
    "startup": {"delayMs": 3000},
    "runtime": {"debug": False, "useReloader": False},
}
frontend_default = {
    "server": {"host": "127.0.0.1", "port": 8080, "url": "http://127.0.0.1:8080"},
    "tls": {"enabled": False, "certFile": "", "keyFile": ""},
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
    for key in ("server", "tls", "startup", "runtime", "api"):
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
backend_tls_enabled = backend["tls"].get("enabled", False)
backend_tls_adhoc = backend["tls"].get("adhoc", True)
backend_tls_cert_file = backend["tls"].get("certFile", "")
backend_tls_key_file = backend["tls"].get("keyFile", "")
backend_debug = backend["runtime"].get("debug", False)
backend_reloader = backend["runtime"].get("useReloader", False)
frontend_host = frontend["server"]["host"]
frontend_port = frontend["server"]["port"]
frontend_url_base = frontend["server"]["url"]
frontend_tls_enabled = frontend["tls"].get("enabled", False)
frontend_tls_cert_file = frontend["tls"].get("certFile", "")
frontend_tls_key_file = frontend["tls"].get("keyFile", "")
frontend_backend_url = frontend["api"]["backendUrl"]

print(delay_ms)
print(backend_host)
print(backend_port)
print(backend_url_base)
print(str(backend_tls_enabled))
print(str(backend_tls_adhoc))
print(backend_tls_cert_file)
print(backend_tls_key_file)
print(str(backend_debug))
print(str(backend_reloader))
print(frontend_host)
print(frontend_port)
print(frontend_url_base)
print(str(frontend_tls_enabled))
print(frontend_tls_cert_file)
print(frontend_tls_key_file)
print(frontend_backend_url)
PY
}

mapfile -t CONFIG_VALUES < <(read_config_defaults)

DEFAULT_DELAY_MS="${CONFIG_VALUES[0]}"
DEFAULT_BACKEND_HOST="${CONFIG_VALUES[1]}"
DEFAULT_BACKEND_PORT="${CONFIG_VALUES[2]}"
DEFAULT_BACKEND_URL_BASE="${CONFIG_VALUES[3]}"
DEFAULT_BACKEND_TLS_ENABLED="${CONFIG_VALUES[4]}"
DEFAULT_BACKEND_TLS_ADHOC="${CONFIG_VALUES[5]}"
DEFAULT_BACKEND_TLS_CERT_FILE="${CONFIG_VALUES[6]}"
DEFAULT_BACKEND_TLS_KEY_FILE="${CONFIG_VALUES[7]}"
DEFAULT_BACKEND_DEBUG="${CONFIG_VALUES[8]}"
DEFAULT_BACKEND_RELOADER="${CONFIG_VALUES[9]}"
DEFAULT_FRONTEND_HOST="${CONFIG_VALUES[10]}"
DEFAULT_FRONTEND_PORT="${CONFIG_VALUES[11]}"
DEFAULT_FRONTEND_URL_BASE="${CONFIG_VALUES[12]}"
DEFAULT_FRONTEND_TLS_ENABLED="${CONFIG_VALUES[13]}"
DEFAULT_FRONTEND_TLS_CERT_FILE="${CONFIG_VALUES[14]}"
DEFAULT_FRONTEND_TLS_KEY_FILE="${CONFIG_VALUES[15]}"
DEFAULT_FRONTEND_BACKEND_URL="${CONFIG_VALUES[16]}"

# --- Parse command-line arguments ---
TLS_OFF=false
BACKEND_TLS_OFF_ARG=false
FRONTEND_TLS_OFF_ARG=false
USE_BACKEND_CERT_FILES_ARG=false
ARG_BACKEND_CERT_FILE=""
ARG_BACKEND_KEY_FILE=""
ARG_DELAY_MS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --tls-off)                TLS_OFF=true;                    shift ;;
        --backend-tls-off)        BACKEND_TLS_OFF_ARG=true;        shift ;;
        --frontend-tls-off)       FRONTEND_TLS_OFF_ARG=true;       shift ;;
        --use-backend-cert-files) USE_BACKEND_CERT_FILES_ARG=true; shift ;;
        --backend-cert-file=*)    ARG_BACKEND_CERT_FILE="${1#*=}"; shift ;;
        --backend-cert-file)      ARG_BACKEND_CERT_FILE="$2";      shift 2 ;;
        --backend-key-file=*)     ARG_BACKEND_KEY_FILE="${1#*=}";  shift ;;
        --backend-key-file)       ARG_BACKEND_KEY_FILE="$2";       shift 2 ;;
        --delay-ms=*)             ARG_DELAY_MS="${1#*=}";          shift ;;
        --delay-ms)               ARG_DELAY_MS="$2";               shift 2 ;;
        [0-9]*)                   ARG_DELAY_MS="$1";               shift ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

DELAY_MS="${ARG_DELAY_MS:-${DELAY_MS:-$DEFAULT_DELAY_MS}}"
BIND_IP="${BIND_IP:-${DEFAULT_FRONTEND_HOST:-$DEFAULT_BACKEND_HOST}}"
BACKEND_PORT="${BACKEND_PORT:-$DEFAULT_BACKEND_PORT}"
FRONTEND_PORT="${FRONTEND_PORT:-$DEFAULT_FRONTEND_PORT}"
BACKEND_DEBUG="${BACKEND_DEBUG:-$DEFAULT_BACKEND_DEBUG}"
BACKEND_RELOADER="${BACKEND_RELOADER:-$DEFAULT_BACKEND_RELOADER}"
BACKEND_TLS_ENABLED="${BACKEND_TLS_ENABLED:-$DEFAULT_BACKEND_TLS_ENABLED}"
BACKEND_TLS_ADHOC="${BACKEND_TLS_ADHOC:-$DEFAULT_BACKEND_TLS_ADHOC}"
BACKEND_TLS_CERT_FILE="${BACKEND_TLS_CERT_FILE:-$DEFAULT_BACKEND_TLS_CERT_FILE}"
BACKEND_TLS_KEY_FILE="${BACKEND_TLS_KEY_FILE:-$DEFAULT_BACKEND_TLS_KEY_FILE}"
FRONTEND_TLS_ENABLED="${FRONTEND_TLS_ENABLED:-$DEFAULT_FRONTEND_TLS_ENABLED}"
FRONTEND_TLS_CERT_FILE="${FRONTEND_TLS_CERT_FILE:-$DEFAULT_FRONTEND_TLS_CERT_FILE}"
FRONTEND_TLS_KEY_FILE="${FRONTEND_TLS_KEY_FILE:-$DEFAULT_FRONTEND_TLS_KEY_FILE}"

# Apply command-line TLS switch overrides
HAS_TLS_SWITCH_OVERRIDE=false

if [[ "$TLS_OFF" == true ]]; then
    BACKEND_TLS_ENABLED="False"
    FRONTEND_TLS_ENABLED="False"
    HAS_TLS_SWITCH_OVERRIDE=true
fi
if [[ "$BACKEND_TLS_OFF_ARG" == true ]]; then
    BACKEND_TLS_ENABLED="False"
    HAS_TLS_SWITCH_OVERRIDE=true
fi
if [[ "$FRONTEND_TLS_OFF_ARG" == true ]]; then
    FRONTEND_TLS_ENABLED="False"
    HAS_TLS_SWITCH_OVERRIDE=true
fi
if [[ "$USE_BACKEND_CERT_FILES_ARG" == true ]]; then
    BACKEND_TLS_ADHOC="False"
    HAS_TLS_SWITCH_OVERRIDE=true
    [[ -n "$ARG_BACKEND_CERT_FILE" ]] && BACKEND_TLS_CERT_FILE="$ARG_BACKEND_CERT_FILE"
    [[ -n "$ARG_BACKEND_KEY_FILE"  ]] && BACKEND_TLS_KEY_FILE="$ARG_BACKEND_KEY_FILE"
fi

# Determine effective protocols
if [[ "${BACKEND_TLS_ENABLED,,}" == "true" ]]; then
    BACKEND_PROTOCOL="https"
else
    BACKEND_PROTOCOL="http"
fi
if [[ "${FRONTEND_TLS_ENABLED,,}" == "true" ]]; then
    FRONTEND_PROTOCOL="https"
else
    FRONTEND_PROTOCOL="http"
fi

if [[ "$HAS_TLS_SWITCH_OVERRIDE" == true ]]; then
    BACKEND_URL="${BACKEND_PROTOCOL}://${BIND_IP}:${BACKEND_PORT}/members"
    FRONTEND_URL="${FRONTEND_PROTOCOL}://${BIND_IP}:${FRONTEND_PORT}/"
    VUE_APP_BACKEND_URL="${BACKEND_PROTOCOL}://${BIND_IP}:${BACKEND_PORT}"
else
    BACKEND_URL="${BACKEND_URL:-${DEFAULT_BACKEND_URL_BASE%/}/members}"
    FRONTEND_URL="${FRONTEND_URL:-${DEFAULT_FRONTEND_URL_BASE%/}/}"
    VUE_APP_BACKEND_URL="${VUE_APP_BACKEND_URL:-$DEFAULT_FRONTEND_BACKEND_URL}"
fi

SLEEP_SECONDS=$(awk "BEGIN {printf \"%.3f\", $DELAY_MS / 1000}")

test_server_url() {
    local url="$1"
    if [[ "$url" == https://* ]]; then
        curl --silent --show-error --max-time 5 --insecure "$url" >/dev/null 2>&1
    else
        curl --silent --show-error --max-time 5 "$url" >/dev/null 2>&1
    fi
}

BACKEND_SSL_CONTEXT_PY="None"
if [[ "${BACKEND_TLS_ENABLED,,}" == "true" ]]; then
    if [[ "${BACKEND_TLS_ADHOC,,}" == "true" ]]; then
        BACKEND_SSL_CONTEXT_PY="'adhoc'"
    else
        CERT_PATH="$BACKEND_TLS_CERT_FILE"
        KEY_PATH="$BACKEND_TLS_KEY_FILE"
        if [[ -z "$CERT_PATH" || -z "$KEY_PATH" ]]; then
            echo "Backend TLS is enabled but cert/key files are missing in backend/server.config.json"
            exit 1
        fi
        if [[ "$CERT_PATH" != /* ]]; then
            CERT_PATH="$BACKEND_DIR/$CERT_PATH"
        fi
        if [[ "$KEY_PATH" != /* ]]; then
            KEY_PATH="$BACKEND_DIR/$KEY_PATH"
        fi
        if [[ ! -f "$CERT_PATH" ]]; then
            echo "Backend TLS certificate not found: $CERT_PATH"
            exit 1
        fi
        if [[ ! -f "$KEY_PATH" ]]; then
            echo "Backend TLS key not found: $KEY_PATH"
            exit 1
        fi
        BACKEND_SSL_CONTEXT_PY="('$CERT_PATH', '$KEY_PATH')"
    fi
fi

(
    cd "$BACKEND_DIR" || exit 1
    nohup "$PYTHON_BIN" -c "import app; app.configure_logging(); app.app.run(host='${BIND_IP}', port=${BACKEND_PORT}, debug=${BACKEND_DEBUG}, use_reloader=${BACKEND_RELOADER}, ssl_context=${BACKEND_SSL_CONTEXT_PY})" >/dev/null 2>&1 &
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
    export VUE_APP_TLS_ENABLED="$FRONTEND_TLS_ENABLED"
    export VUE_APP_TLS_CERT_FILE="$FRONTEND_TLS_CERT_FILE"
    export VUE_APP_TLS_KEY_FILE="$FRONTEND_TLS_KEY_FILE"
    nohup npx --yes npm@11.12.1 run dev -- --host "$BIND_IP" --port "$FRONTEND_PORT" >/dev/null 2>&1 &
    echo $! > "$SCRIPT_DIR/.frontend.pid"
)

sleep "$SLEEP_SECONDS"

if test_server_url "$FRONTEND_URL"; then
    echo "Server Running"
else
    echo "Server Not Running"
    exit 1
fi
