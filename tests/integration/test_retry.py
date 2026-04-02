"""Integration test — retry logic for transient HTTP errors."""
import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest

from src.config_loader import Source


class TestRequestWithRetry:
    def test_returns_response_on_success(self):
        from src.module1_scanner.scanners.api import _request_with_retry

        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_resp

        resp = asyncio.get_event_loop().run_until_complete(
            _request_with_retry(mock_client, "https://example.com/api", "test_api")
        )
        assert resp.status_code == 200
        assert mock_client.get.call_count == 1

    def test_retries_on_429(self):
        from src.module1_scanner.scanners.api import _request_with_retry

        resp_429 = AsyncMock(spec=httpx.Response)
        resp_429.status_code = 429
        resp_429.headers = {}
        resp_429.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429", request=AsyncMock(), response=resp_429
        )

        resp_200 = AsyncMock(spec=httpx.Response)
        resp_200.status_code = 200
        resp_200.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = [resp_429, resp_200]

        resp = asyncio.get_event_loop().run_until_complete(
            _request_with_retry(mock_client, "https://example.com/api", "test_api")
        )
        assert resp.status_code == 200
        assert mock_client.get.call_count == 2

    def test_retries_on_500(self):
        from src.module1_scanner.scanners.api import _request_with_retry

        resp_500 = AsyncMock(spec=httpx.Response)
        resp_500.status_code = 500
        resp_500.headers = {}
        resp_500.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=AsyncMock(), response=resp_500
        )

        resp_200 = AsyncMock(spec=httpx.Response)
        resp_200.status_code = 200
        resp_200.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = [resp_500, resp_200]

        resp = asyncio.get_event_loop().run_until_complete(
            _request_with_retry(mock_client, "https://example.com/api", "test_api")
        )
        assert resp.status_code == 200
        assert mock_client.get.call_count == 2

    def test_retries_on_503(self):
        from src.module1_scanner.scanners.api import _request_with_retry

        resp_503 = AsyncMock(spec=httpx.Response)
        resp_503.status_code = 503
        resp_503.headers = {}
        resp_503.raise_for_status.side_effect = httpx.HTTPStatusError(
            "503", request=AsyncMock(), response=resp_503
        )

        resp_200 = AsyncMock(spec=httpx.Response)
        resp_200.status_code = 200
        resp_200.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = [resp_503, resp_200]

        resp = asyncio.get_event_loop().run_until_complete(
            _request_with_retry(mock_client, "https://example.com/api", "test_api")
        )
        assert resp.status_code == 200

    def test_raises_after_max_retries(self):
        from src.module1_scanner.scanners.api import _request_with_retry

        resp_429 = AsyncMock(spec=httpx.Response)
        resp_429.status_code = 429
        resp_429.headers = {}
        resp_429.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429", request=AsyncMock(), response=resp_429
        )

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = resp_429

        with pytest.raises(httpx.HTTPStatusError):
            asyncio.get_event_loop().run_until_complete(
                _request_with_retry(mock_client, "https://example.com/api", "test_api")
            )
        assert mock_client.get.call_count == 3

    def test_does_not_retry_on_400(self):
        from src.module1_scanner.scanners.api import _request_with_retry

        resp_400 = AsyncMock(spec=httpx.Response)
        resp_400.status_code = 400
        resp_400.headers = {}
        resp_400.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400", request=AsyncMock(), response=resp_400
        )

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = resp_400

        with pytest.raises(httpx.HTTPStatusError):
            asyncio.get_event_loop().run_until_complete(
                _request_with_retry(mock_client, "https://example.com/api", "test_api")
            )
        assert mock_client.get.call_count == 1

    def test_respects_retry_after_header(self):
        from src.module1_scanner.scanners.api import _request_with_retry

        resp_429 = AsyncMock(spec=httpx.Response)
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "1"}
        resp_429.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429", request=AsyncMock(), response=resp_429
        )

        resp_200 = AsyncMock(spec=httpx.Response)
        resp_200.status_code = 200
        resp_200.raise_for_status = lambda: None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = [resp_429, resp_200]

        resp = asyncio.get_event_loop().run_until_complete(
            _request_with_retry(mock_client, "https://example.com/api", "test_api")
        )
        assert resp.status_code == 200
