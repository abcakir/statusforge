import logging
import time

import httpx

logger = logging.getLogger(__name__)

DEGRADED_LATENCY_MS = 2000


async def probe_http(url: str, timeout: int) -> dict:
    start = time.monotonic()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout, follow_redirects=True)
        latency_ms = (time.monotonic() - start) * 1000

        if response.status_code >= 500:
            return {"status": "DOWN", "latency_ms": latency_ms, "status_code": response.status_code, "error": f"HTTP {response.status_code}"}
        if latency_ms > DEGRADED_LATENCY_MS:
            return {"status": "DEGRADED", "latency_ms": latency_ms, "status_code": response.status_code, "error": None}
        return {"status": "UP", "latency_ms": latency_ms, "status_code": response.status_code, "error": None}

    except httpx.TimeoutException:
        return {"status": "DOWN", "latency_ms": None, "status_code": None, "error": "Connection timed out"}
    except Exception as e:
        return {"status": "DOWN", "latency_ms": None, "status_code": None, "error": str(e)}
