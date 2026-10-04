"""Keep the free-tier Render instance awake with a periodic self-ping.

Render free spins the service down after ~15 minutes without inbound
traffic, so the first request of a new session pays an 8-25 s cold start
and the client gives up at 10 s (timeout toast, half-applied transport).
Pinging our own *public* URL from a background task is inbound traffic to
the router, which keeps the instance warm for as long as the process
runs. GitHub's schedule cron proved unreliable for this repo (0 fires
after re-registration) and the in-page ping only helps while a tab is
open - this loop needs neither.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import httpx

from migmusic.core import get_logger

logger = get_logger(__name__)

#: Render sleeps after 15 idle minutes; ping well inside that window so the
#: first real request never pays the full cold start.
KEEP_ALIVE_INTERVAL_S = 240.0


def keep_alive_url(base_url: str) -> str:
    """Public health URL whose requests count as traffic (router-visible)."""
    return f"{base_url.rstrip('/')}/api/health"


def make_pinger(client: httpx.AsyncClient, base_url: str) -> Callable[[], Awaitable[None]]:
    """Build the ping coroutine: one GET at the public health URL."""
    url = keep_alive_url(base_url)

    async def ping() -> None:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()

    return ping


async def keep_alive_loop(
    ping: Callable[[], Awaitable[None]],
    *,
    interval_s: float = KEEP_ALIVE_INTERVAL_S,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> None:
    """Ping forever on schedule; a failed ping is logged, never fatal."""
    while True:
        await sleep(interval_s)
        try:
            await ping()
        except Exception:
            logger.warning("keep_alive_ping_failed", exc_info=True)
