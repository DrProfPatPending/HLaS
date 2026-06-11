#!/usr/bin/env bash
# Fetches the Caddy local root CA cert from a remote HLaS server via SSH
# and installs it into the macOS Login Keychain so that Safari (and other
# system-level TLS clients) trust the dev server. No sudo required.
#
# Usage:
#   ./trust_caddy_mac.sh [OPTIONS]
#
# Options:
#   -h HOST       SSH hostname or IP  (default: hlastest)
#   -u USER       SSH username        (default: rob)
#   -p PATH       Remote HLaS dir     (default: /opt/hlas)
#   --help        Show this help
#
# Requires sudo to write to the System Keychain.
# Run once; re-run if Caddy regenerates its root CA.
set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────────────────
SSH_HOST="hlastest"
SSH_USER="rob"
REMOTE_DIR="/opt/hlas"

# ── Argument parsing ──────────────────────────────────────────────────────────
usage() {
    sed -n '/^# Usage:/,/^[^#]/p' "$0" | grep '^#' | sed 's/^# \{0,1\}//'
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h) SSH_HOST="$2"; shift 2 ;;
        -u) SSH_USER="$2"; shift 2 ;;
        -p) REMOTE_DIR="$2"; shift 2 ;;
        --help) usage ;;
        *) echo "Unknown option: $1" >&2; usage ;;
    esac
done

CERT_NAME="hlastest-caddy-local"
TMP_CERT="/tmp/${CERT_NAME}.crt"
REMOTE_CERT_PATH="/data/caddy/pki/authorities/local/root.crt"
COMPOSE_FILE="${REMOTE_DIR}/docker-compose.prod.yml"

echo "Fetching Caddy root CA certificate from ${SSH_USER}@${SSH_HOST} ..."
ssh "${SSH_USER}@${SSH_HOST}" \
    "docker compose -f '${COMPOSE_FILE}' exec -T caddy cat '${REMOTE_CERT_PATH}'" \
    > "$TMP_CERT"

SUBJECT=$(openssl x509 -in "$TMP_CERT" -noout -subject 2>/dev/null | sed 's/subject=//')
THUMBPRINT=$(openssl x509 -in "$TMP_CERT" -noout -fingerprint -sha256 2>/dev/null | sed 's/.*=//')
EXPIRY=$(openssl x509 -in "$TMP_CERT" -noout -enddate 2>/dev/null | sed 's/notAfter=//')

echo ""
echo "  Subject   : $SUBJECT"
echo "  SHA-256   : $THUMBPRINT"
echo "  Expires   : $EXPIRY"
echo ""

LOGIN_KEYCHAIN="$HOME/Library/Keychains/login.keychain-db"

# Remove any previously installed copy with the same name to avoid duplicates.
if security find-certificate -c "$CERT_NAME" "$LOGIN_KEYCHAIN" &>/dev/null; then
    echo "Removing existing certificate '${CERT_NAME}' from Login Keychain..."
    security delete-certificate -c "$CERT_NAME" "$LOGIN_KEYCHAIN"
fi

echo "Installing certificate into macOS Login Keychain (no sudo required)..."
security add-trusted-cert \
    -r trustRoot \
    -k "$LOGIN_KEYCHAIN" \
    "$TMP_CERT"

echo ""
echo "Certificate '${CERT_NAME}' installed and trusted in the Login Keychain."
echo "Quit and relaunch Safari, then open https://${SSH_HOST} to verify."
