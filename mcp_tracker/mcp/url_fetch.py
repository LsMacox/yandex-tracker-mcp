"""SSRF-safe URL fetcher for attachment uploads via `source_url`.

Guardrails (all enforced):
- HTTPS only — plain HTTP is rejected
- Host must match the operator-configured allowlist (exact or `*.suffix`)
- Redirects are NOT followed (would bypass the allowlist)
- Response bytes are capped — we stream and abort once the cap is crossed
- Request has a wall-clock timeout

The feature is off by default: with no allowlist configured `source_url` is
rejected up-front so an attacker who tricks an LLM into calling
`issue_attachments(action="upload", source_url=...)` can't probe internal
services.
"""

from __future__ import annotations

import os.path
from urllib.parse import unquote, urlparse

import aiohttp


class UrlFetchError(Exception):
    """Raised when a remote-URL attachment fetch is refused or fails."""


def _host_allowed(host: str, allowed: list[str]) -> bool:
    host = host.lower()
    for raw in allowed:
        domain = raw.strip().lower()
        if not domain:
            continue
        if domain.startswith("*."):
            suffix = domain[1:]  # `.example.com`
            bare = domain[2:]  # `example.com`
            if host == bare or host.endswith(suffix):
                return True
        elif host == domain:
            return True
    return False


async def fetch_attachment(
    url: str,
    *,
    allowed_domains: list[str] | None,
    max_bytes: int,
    timeout_seconds: float,
) -> tuple[bytes, str | None]:
    """Download an attachment from a whitelisted URL.

    Returns `(bytes, suggested_filename)` — filename is derived from the URL
    path (caller may override). Raises `UrlFetchError` on any failure.
    """
    if not allowed_domains:
        raise UrlFetchError(
            "source_url is disabled — set TRACKER_ATTACHMENT_URL_ALLOWED_DOMAINS "
            "(comma-separated hosts or `*.suffix`) to enable."
        )

    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise UrlFetchError(
            f"Only https URLs are allowed, got scheme: {parsed.scheme!r}"
        )
    if not parsed.hostname:
        raise UrlFetchError("URL has no host.")
    if not _host_allowed(parsed.hostname, allowed_domains):
        raise UrlFetchError(f"Host `{parsed.hostname}` is not in the allowlist.")

    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, allow_redirects=False) as resp:
                if resp.status >= 300 and resp.status < 400:
                    raise UrlFetchError(
                        f"Redirect ({resp.status}) not followed — allowlist "
                        "must be satisfied by the original URL."
                    )
                if resp.status != 200:
                    raise UrlFetchError(f"HTTP {resp.status} from {url}")

                # Streaming size check — don't trust Content-Length.
                buffer = bytearray()
                async for chunk in resp.content.iter_chunked(64 * 1024):
                    buffer.extend(chunk)
                    if len(buffer) > max_bytes:
                        raise UrlFetchError(
                            f"Response exceeds max size ({max_bytes} bytes)."
                        )
    except aiohttp.ClientError as e:
        raise UrlFetchError(f"Network error: {e}") from e

    path = unquote(parsed.path or "")
    suggested = os.path.basename(path.rstrip("/")) or None
    return bytes(buffer), suggested
