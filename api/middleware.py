import time
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.core.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------

# Structure: { "ip_address": [timestamp1, timestamp2, ...] }
_rate_limits: dict[str, list[float]] = defaultdict(list)

MAX_REQUESTS = 100
WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Lightweight in-memory per-IP rate limiter.
    Allows up to 100 requests per 60-second window.
    Returns HTTP 429 with Retry-After header on breach.
    """
    async def dispatch(self, request: Request, call_next):
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        now = time.time()

        # Clean stale timestamps outside the rolling window
        _rate_limits[client_ip] = [
            ts for ts in _rate_limits[client_ip]
            if now - ts < WINDOW_SECONDS
        ]

        # Prevent memory leaks by pruning empty IP entries
        if not _rate_limits[client_ip]:
            del _rate_limits[client_ip]

        if len(_rate_limits[client_ip]) >= MAX_REQUESTS:
            logger.warning("Rate limit exceeded | IP=%s", client_ip)
            retry_after = int(WINDOW_SECONDS - (now - _rate_limits[client_ip][0]))
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": str(max(retry_after, 1))}
            )

        _rate_limits[client_ip].append(now)
        return await call_next(request)


# ---------------------------------------------------------------------------
# Bot Protection
# ---------------------------------------------------------------------------

# Known automated tool signatures to block
_BLOCKED_UA_PATTERNS = [
    "python-requests",
    "python-urllib",
    "wget",
    "curl/",
    "go-http-client",
    "libwww-perl",
    "scrapy",
    "httpx",
    "aiohttp",
]

# Substrings that indicate a real browser User-Agent — always allow
_BROWSER_UA_MARKERS = [
    "mozilla",
    "chrome",
    "safari",
    "firefox",
    "edge",
    "opera",
    "vercel",
]


class BotProtectionMiddleware(BaseHTTPMiddleware):
    """
    Lightweight bot protection layer.
    Blocks requests with:
      - Missing User-Agent header
      - Known automated tool signatures (curl, wget, python-requests, etc.)

    Whitelists:
      - All real browser User-Agents (Mozilla, Chrome, Safari, Firefox, Edge)
      - Vercel health checks and frontend traffic
    """
    async def dispatch(self, request: Request, call_next):
        # Skip protection on health/meta paths
        if request.url.path in ("/", "/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        user_agent = request.headers.get("user-agent", "").strip()

        # 1. Block completely missing User-Agent
        if not user_agent:
            client_ip = request.headers.get("x-forwarded-for", "unknown").split(",")[0].strip()
            logger.warning("Bot blocked: empty User-Agent | IP=%s | Path=%s", client_ip, request.url.path)
            return JSONResponse(
                status_code=403,
                content={"detail": "Forbidden"}
            )

        ua_lower = user_agent.lower()

        # 2. Whitelist real browsers first — never block them
        if any(marker in ua_lower for marker in _BROWSER_UA_MARKERS):
            return await call_next(request)

        # 3. Block known automated tool signatures
        if any(pattern in ua_lower for pattern in _BLOCKED_UA_PATTERNS):
            client_ip = request.headers.get("x-forwarded-for", "unknown").split(",")[0].strip()
            logger.warning(
                "Bot blocked: suspicious User-Agent | IP=%s | UA=%s | Path=%s",
                client_ip, user_agent, request.url.path
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Forbidden"}
            )

        return await call_next(request)

