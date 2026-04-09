import time
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Simple in-memory rate limit tracker
# Structure: { "ip_address": [timestamp1, timestamp2, ...] }
_rate_limits: dict[str, list[float]] = defaultdict(list)

MAX_REQUESTS = 60
WINDOW_SECONDS = 60

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Lightweight, strictly in-memory per-IP Rate Limiting boundary.
    Configured precisely to allow 60 requests per 60 seconds blocking abusive pings.
    """
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # 1. Clean timestamps older than the explicit 60-second window bounds
        _rate_limits[client_ip] = [
            ts for ts in _rate_limits[client_ip] 
            if now - ts < WINDOW_SECONDS
        ]
        
        # 2. Halt if the rate limit cap is successfully exceeded natively
        if len(_rate_limits[client_ip]) >= MAX_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."}
            )
            
        # 3. Securely record the timestamp sequentially onto tracking records
        _rate_limits[client_ip].append(now)

        return await call_next(request)
