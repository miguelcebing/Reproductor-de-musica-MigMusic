#!/usr/bin/env bash
# One-shot server provisioning for MigMusic. Safe to re-run.
# Usage: sudo SSH_SOURCE=200.1.2.3/32 bash provision.sh
set -euo pipefail

APP_USER="${APP_USER:-migmusic}"
APP_DIR="${APP_DIR:-/opt/migmusic}"
ENV_DIR="${ENV_DIR:-/etc/migmusic}"
# CIDR allowed to reach port 22. Defaults to the whole internet (key-only auth
# plus fail2ban); pass your own IP to lock SSH down further.
SSH_SOURCE="${SSH_SOURCE:-0.0.0.0/0}"

export DEBIAN_FRONTEND=noninteractive

echo "==> Installing packages"
apt-get update -q
apt-get install -y -q --no-install-recommends \
  nginx certbot python3-certbot-nginx fail2ban ufw unattended-upgrades \
  curl ca-certificates rsync git postgresql-client

echo "==> Installing uv (Python package manager used by the app)"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
fi
uv --version

echo "==> Adding a 2G swap file (small instances can OOM during builds)"
if [ "$(awk '/^SwapTotal/ {print $2}' /proc/meminfo)" = "0" ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile >/dev/null
  swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >>/etc/fstab
fi

echo "==> Creating the unprivileged service user (${APP_USER})"
# The home directory must live outside /home: the systemd unit sets
# ProtectHome=yes, so /home becomes unreadable, and libpq probes
# ~/.postgresql/postgresql.crt on every connect. Under /home that probe fails
# with EACCES (fatal) instead of ENOENT (ignored), killing every pooled
# connection with PoolTimeout.
APP_HOME="/var/lib/${APP_USER}"
if ! id -u "${APP_USER}" >/dev/null 2>&1; then
  useradd --system --create-home --home-dir "${APP_HOME}" --shell /usr/sbin/nologin "${APP_USER}"
elif [ "$(getent passwd "${APP_USER}" | cut -d: -f6)" != "${APP_HOME}" ]; then
  install -d -o "${APP_USER}" -g "${APP_USER}" -m 0755 "${APP_HOME}"
  systemctl stop "${APP_USER}.service" 2>/dev/null || true
  usermod --home "${APP_HOME}" "${APP_USER}"
fi
install -d -o "${APP_USER}" -g "${APP_USER}" -m 0755 "${APP_DIR}"
install -d -o root -g "${APP_USER}" -m 0750 "${ENV_DIR}"

echo "==> Enabling security updates"
cat >/etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
systemctl enable --now unattended-upgrades 2>/dev/null || true

echo "==> Configuring the host firewall (only 22, 80, 443)"
ufw default deny incoming
ufw default allow outgoing
ufw allow from "${SSH_SOURCE}" to any port 22 proto tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable
ufw status verbose

echo "==> Enabling fail2ban for sshd"
systemctl enable --now fail2ban
fail2ban-client status sshd >/dev/null 2>&1 || true

echo "==> Enabling nginx"
systemctl enable --now nginx
# Ubuntu ships a default site that claims every unmatched Host header. Our
# server block is the only one we want answering on port 80.
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "==> Provisioning finished"
