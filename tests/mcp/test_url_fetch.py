"""Tests for the SSRF-safe URL fetcher."""

import aiohttp
import pytest
from aioresponses import aioresponses

from mcp_tracker.mcp.url_fetch import UrlFetchError, _host_allowed, fetch_attachment


class TestHostAllowed:
    @pytest.mark.parametrize(
        "host,allowed,ok",
        [
            ("files.example.com", ["files.example.com"], True),
            ("Files.Example.COM", ["files.example.com"], True),
            ("attacker.com", ["files.example.com"], False),
            ("sub.example.com", ["*.example.com"], True),
            ("deep.sub.example.com", ["*.example.com"], True),
            ("example.com", ["*.example.com"], True),
            ("evilexample.com", ["*.example.com"], False),
            ("host", [], False),
        ],
    )
    def test_matches(self, host: str, allowed: list[str], ok: bool) -> None:
        assert _host_allowed(host, allowed) is ok


class TestFetchAttachment:
    async def test_disabled_without_allowlist(self) -> None:
        with pytest.raises(UrlFetchError, match="disabled"):
            await fetch_attachment(
                "https://example.com/f.bin",
                allowed_domains=None,
                max_bytes=1024,
                timeout_seconds=5,
            )

    async def test_rejects_http(self) -> None:
        with pytest.raises(UrlFetchError, match="https"):
            await fetch_attachment(
                "http://example.com/f.bin",
                allowed_domains=["example.com"],
                max_bytes=1024,
                timeout_seconds=5,
            )

    async def test_rejects_disallowed_host(self) -> None:
        with pytest.raises(UrlFetchError, match="not in the allowlist"):
            await fetch_attachment(
                "https://attacker.com/f.bin",
                allowed_domains=["example.com"],
                max_bytes=1024,
                timeout_seconds=5,
            )

    async def test_happy_path(self) -> None:
        with aioresponses() as m:
            m.get(
                "https://files.example.com/report.pdf",
                status=200,
                body=b"PDF-bytes-here",
            )
            data, filename = await fetch_attachment(
                "https://files.example.com/report.pdf",
                allowed_domains=["files.example.com"],
                max_bytes=1024 * 1024,
                timeout_seconds=5,
            )
            assert data == b"PDF-bytes-here"
            assert filename == "report.pdf"

    async def test_redirect_not_followed(self) -> None:
        with aioresponses() as m:
            m.get(
                "https://files.example.com/r",
                status=302,
                headers={"Location": "https://attacker.com/f"},
            )
            with pytest.raises(UrlFetchError, match="Redirect"):
                await fetch_attachment(
                    "https://files.example.com/r",
                    allowed_domains=["files.example.com"],
                    max_bytes=1024,
                    timeout_seconds=5,
                )

    async def test_size_cap_enforced(self) -> None:
        body = b"x" * (10 * 1024)
        with aioresponses() as m:
            m.get(
                "https://files.example.com/big.bin",
                status=200,
                body=body,
            )
            with pytest.raises(UrlFetchError, match="max size"):
                await fetch_attachment(
                    "https://files.example.com/big.bin",
                    allowed_domains=["files.example.com"],
                    max_bytes=5 * 1024,
                    timeout_seconds=5,
                )

    async def test_network_error_wrapped(self) -> None:
        with aioresponses() as m:
            m.get(
                "https://files.example.com/f.bin",
                exception=aiohttp.ClientConnectionError("boom"),
            )
            with pytest.raises(UrlFetchError, match="Network error"):
                await fetch_attachment(
                    "https://files.example.com/f.bin",
                    allowed_domains=["files.example.com"],
                    max_bytes=1024,
                    timeout_seconds=5,
                )
