from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.monitoring.probe import probe_http


def _mock_client(status_code: int, latency_seconds: float = 0.1):
    mock_response = MagicMock()
    mock_response.status_code = status_code

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm, latency_seconds


async def test_probe_returns_up_on_200():
    cm, _ = _mock_client(200)
    with patch("httpx.AsyncClient", return_value=cm):
        result = await probe_http("https://example.com", 10)

    assert result["status"] == "UP"
    assert result["status_code"] == 200
    assert result["error"] is None
    assert result["latency_ms"] is not None


async def test_probe_returns_up_on_201():
    cm, _ = _mock_client(201)
    with patch("httpx.AsyncClient", return_value=cm):
        result = await probe_http("https://example.com", 10)

    assert result["status"] == "UP"


async def test_probe_returns_up_on_404():
    cm, _ = _mock_client(404)
    with patch("httpx.AsyncClient", return_value=cm):
        result = await probe_http("https://example.com", 10)

    assert result["status"] == "UP"
    assert result["status_code"] == 404


async def test_probe_returns_down_on_500():
    cm, _ = _mock_client(500)
    with patch("httpx.AsyncClient", return_value=cm):
        result = await probe_http("https://example.com", 10)

    assert result["status"] == "DOWN"
    assert result["status_code"] == 500
    assert "500" in result["error"]


async def test_probe_returns_down_on_503():
    cm, _ = _mock_client(503)
    with patch("httpx.AsyncClient", return_value=cm):
        result = await probe_http("https://example.com", 10)

    assert result["status"] == "DOWN"


async def test_probe_returns_down_on_timeout():
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_client)
    cm.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=cm):
        result = await probe_http("https://example.com", 10)

    assert result["status"] == "DOWN"
    assert result["latency_ms"] is None
    assert "timed out" in result["error"]


async def test_probe_returns_down_on_connection_error():
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_client)
    cm.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=cm):
        result = await probe_http("https://example.com", 10)

    assert result["status"] == "DOWN"
    assert result["latency_ms"] is None


async def test_probe_returns_degraded_on_high_latency():
    cm, _ = _mock_client(200)
    with patch("httpx.AsyncClient", return_value=cm), \
         patch("time.monotonic", side_effect=[0.0, 2.5]):
        result = await probe_http("https://example.com", 10)

    assert result["status"] == "DEGRADED"
    assert result["latency_ms"] == pytest.approx(2500.0)


async def test_probe_latency_is_recorded():
    cm, _ = _mock_client(200)
    with patch("httpx.AsyncClient", return_value=cm), \
         patch("time.monotonic", side_effect=[0.0, 0.123]):
        result = await probe_http("https://example.com", 10)

    assert result["latency_ms"] == pytest.approx(123.0)
