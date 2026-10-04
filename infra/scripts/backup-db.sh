#!/usr/bin/env bash
# Nightly logical backup of the MigMusic database (Neon/PostgreSQL).
# Installed as /usr/local/bin/migmusic-backup.sh and run by a systemd timer.
set -euo pipefail

ENV_FILE="${ENV_FILE:-/etc/migmusic/migmusic.env}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/migmusic}"
KEEP_DAYS="${KEEP_DAYS:-14}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "error: ${ENV_FILE} not found" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "${ENV_FILE}"
if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "error: DATABASE_URL is empty in ${ENV_FILE}" >&2
  exit 1
fi

command -v pg_dump >/dev/null 2>&1 || {
  echo "error: pg_dump not installed (postgresql-client)" >&2
  exit 1
}

install -d -m 0750 -o root -g migmusic "${BACKUP_DIR}"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="${BACKUP_DIR}/migmusic-${stamp}.sql.gz"

pg_dump --no-owner --no-privileges "${DATABASE_URL}" | gzip -9 >"${target}"
chmod 0640 "${target}"
chown root:migmusic "${target}"

# Keep a rolling window so a bad migration can be undone without unbounded disk use.
find "${BACKUP_DIR}" -name 'migmusic-*.sql.gz' -mtime +"${KEEP_DAYS}" -delete

echo "wrote ${target} ($(du -h "${target}" | cut -f1))"
