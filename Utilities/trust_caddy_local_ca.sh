#!/usr/bin/env bash
set -euo pipefail

CERT_NAME="hlastest-caddy-local"
TMP_CERT="/tmp/${CERT_NAME}.crt"
SYSTEM_CERT="/usr/local/share/ca-certificates/${CERT_NAME}.crt"

cd /opt/hlas

echo "Exporting Caddy local root certificate..."
docker compose -f docker-compose.prod.yml exec -T caddy \
  cat /data/caddy/pki/authorities/local/root.crt > "$TMP_CERT"

echo "Installing certificate into system trust store..."
sudo cp "$TMP_CERT" "$SYSTEM_CERT"
sudo update-ca-certificates

echo "Installed: $SYSTEM_CERT"

echo ""
echo "If you use Firefox, install NSS tools and import cert to your profile too:"
echo "  sudo apt-get update && sudo apt-get install -y libnss3-tools"
echo "  certutil -A -n '${CERT_NAME}' -t 'C,,' -i '$TMP_CERT' -d sql:\$HOME/.mozilla/firefox/<profile>.default-release"
echo ""
echo "Then fully restart your browser and re-open https://hlastest/admin"
