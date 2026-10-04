#!/usr/bin/env bash
# Applies a release that was already extracted into /opt/migmusic.
# Run as root: sudo bash apply-deploy.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/migmusic}"
APP_USER="${APP_USER:-migmusic}"
ENV_FILE="${ENV_FILE:-/etc/migmusic/migmusic.env}"

if [[ ! -f "${APP_DIR}/backend/uv.lock" ]]; then
  echo "error: ${APP_DIR}/backend/uv.lock not found - extract the release first" >&2
  exit 1
fi
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "error: ${ENV_FILE} missing - copy infra/env/migmusic.env.example and fill it in" >&2
  exit 1
fi

echo "==> Installing the Python environment"
export UV_LINK_MODE=copy
cd "${APP_DIR}/backend"
if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv is not installed (re-run provision.sh)" >&2
  exit 1
fi
uv sync --frozen --no-dev

echo "==> Installing Nginx configuration"
install -d -o root -g root -m 0755 /etc/nginx/snippets
install -o root -g root -m 0644 "${APP_DIR}/infra/nginx/migmusic.conf" /etc/nginx/conf.d/migmusic.conf
install -o root -g root -m 0644 "${APP_DIR}/infra/nginx/security-headers.conf" /etc/nginx/snippets/security-headers.conf
nginx -t
systemctl reload nginx

echo "==> Installing the systemd unit"
install -o root -g root -m 0644 "${APP_DIR}/infra/systemd/migmusic.service" /etc/systemd/system/migmusic.service
systemctl daemon-reload
systemctl enable migmusic >/dev/null 2>&1

echo "==> Installing the nightly database backup"
install -o root -g root -m 0750 "${APP_DIR}/infra/scripts/backup-db.sh" /usr/local/bin/migmusic-backup.sh
install -o root -g root -m 0644 "${APP_DIR}/infra/systemd/migmusic-backup.service" /etc/systemd/system/migmusic-backup.service
install -o root -g root -m 0644 "${APP_DIR}/infra/systemd/migmusic-backup.timer" /etc/systemd/system/migmusic-backup.timer
systemctl daemon-reload
systemctl enable --now migmusic-backup.timer >/dev/null 2>&1

echo "==> Giving the app user ownership of the release"
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

echo "==> Restarting the API"
systemctl restart migmusic
sleep 3
systemctl --no-pager --full status migmusic | head -n 12

echo "==> Health check"
for _ in 1 2 3 4 5; do
  if curl -fsS --max-time 5 http://127.0.0.1:8000/health >/dev/null; then
    echo "API is up"
    exit 0
  fi
  sleep 2
done
echo "error: the API did not answer /health" >&2
journalctl -u migmusic -n 40 --no-pager >&2 || true
exit 1
