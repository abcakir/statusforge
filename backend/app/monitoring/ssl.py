import asyncio
import logging
import socket
import ssl
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


async def check_ssl_certificate(url: str, timeout: int = 10) -> dict:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return {"checked": False}

    hostname = parsed.hostname
    port = parsed.port or 443

    def _fetch_cert():
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                return ssock.getpeercert()

    try:
        loop = asyncio.get_event_loop()
        cert = await loop.run_in_executor(None, _fetch_cert)
        expires_at = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        days_remaining = (expires_at - datetime.utcnow()).days
        return {
            "checked": True,
            "valid": True,
            "expires_at": expires_at,
            "days_remaining": days_remaining,
        }
    except ssl.SSLCertVerificationError as e:
        logger.warning("SSL cert invalid for %s: %s", url, e)
        return {"checked": True, "valid": False, "expires_at": None, "days_remaining": None}
    except Exception as e:
        logger.warning("SSL check failed for %s: %s", url, e)
        return {"checked": True, "valid": False, "expires_at": None, "days_remaining": None}
