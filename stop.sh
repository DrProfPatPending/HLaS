#!/usr/bin/env bash
set -u

BACKEND_PORT="${BACKEND_PORT:-5000}"
FRONTEND_PORT="${FRONTEND_PORT:-8080}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

stop_by_pid_file() {
    local pid_file="$1"

    if [[ ! -f "$pid_file" ]]; then
        return 1
    fi

    local pid
    pid="$(cat "$pid_file" 2>/dev/null)"

    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
    fi

    rm -f "$pid_file"
    return 0
}

stop_by_port() {
    local port="$1"
    local pids

    pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
    if [[ -z "$pids" ]]; then
        pids="$(ss -ltnp 2>/dev/null | awk -v p=":$port" '$4 ~ p {print $NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | sort -u)"
    fi

    if [[ -z "$pids" ]]; then
        return 1
    fi

    for pid in $pids; do
        kill "$pid" 2>/dev/null || true
    done

    return 0
}

backend_stopped=1
frontend_stopped=1

if stop_by_pid_file "$SCRIPT_DIR/.backend.pid"; then
    backend_stopped=0
elif stop_by_port "$BACKEND_PORT"; then
    backend_stopped=0
fi

if stop_by_pid_file "$SCRIPT_DIR/.frontend.pid"; then
    frontend_stopped=0
elif stop_by_port "$FRONTEND_PORT"; then
    frontend_stopped=0
fi

if [[ $backend_stopped -eq 0 || $frontend_stopped -eq 0 ]]; then
    echo "Servers Stopped"
else
    echo "No Running Servers Found"
fi
