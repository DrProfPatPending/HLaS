#!/usr/bin/env bash
# Exports the Caddy local root CA certificate from the running Docker container.
# Copy the output .crt file to your Windows machine, then run:
#   install_hlastest_caddy_root_cert.ps1 -CertPath .\hlastest-caddy-root.crt
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.prod.yml"
OUT_FILE="${SCRIPT_DIR}/hlastest-caddy-root.crt"

echo "Exporting Caddy local root certificate..."
docker compose -f "$COMPOSE_FILE" exec -T caddy \
    cat /data/caddy/pki/authorities/local/root.crt > "$OUT_FILE"

SUBJECT=$(openssl x509 -in "$OUT_FILE" -noout -subject 2>/dev/null | sed 's/subject=//')
THUMBPRINT=$(openssl x509 -in "$OUT_FILE" -noout -fingerprint -sha256 2>/dev/null | sed 's/.*=//')
EXPIRY=$(openssl x509 -in "$OUT_FILE" -noout -enddate 2>/dev/null | sed 's/notAfter=//')

echo ""
echo "Certificate exported to: $OUT_FILE"
echo "  Subject   : $SUBJECT"
echo "  SHA-256   : $THUMBPRINT"
echo "  Expires   : $EXPIRY"
echo ""
echo "Copy this file to your Windows machine, then run (as Administrator):"
echo "  .\\install_hlastest_caddy_root_cert.ps1 -CertPath .\\hlastest-caddy-root.crt -StoreScope LocalMachine"
