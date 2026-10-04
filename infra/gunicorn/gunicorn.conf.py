"""Gunicorn configuration for the MigMusic API.

Two workers are enough for this workload: the API is I/O bound (Spotify,
YouTube Music, LRCLIB, PostgreSQL) and a small instance cannot use more.
"""

from __future__ import annotations

# Loopback only: Nginx is the sole caller and sits on the same host.
bind = "127.0.0.1:8000"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"

# A worker that serves no response for `timeout` seconds is killed and replaced.
timeout = 60
graceful_timeout = 30
keepalive = 5

# Recycle workers after a few thousand requests so a slow leak cannot grow.
max_requests = 1000
max_requests_jitter = 100

# Trust `X-Forwarded-*` only from Nginx on this machine.
forwarded_allow_ips = "127.0.0.1"

accesslog = "-"
errorlog = "-"
loglevel = "info"
