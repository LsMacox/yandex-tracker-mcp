"""Tests for transient-error retries on GET requests."""

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import TrackerAPIError


class TestGetRetries:
    async def test_retries_on_429_then_succeeds(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-1",
                status=429,
                headers={"Retry-After": "0"},
            )
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-1",
                payload={"key": "TEST-1", "summary": "Recovered"},
            )

            result = await tracker_client.issue_get("TEST-1")

        assert result.key == "TEST-1"

    async def test_gives_up_after_retries_exhausted(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            for _ in range(3):  # initial attempt + 2 retries
                m.get(
                    "https://api.tracker.yandex.net/v3/issues/TEST-1",
                    status=503,
                    headers={"Retry-After": "0"},
                )

            try:
                await tracker_client.issue_get("TEST-1")
            except TrackerAPIError as exc:
                assert exc.status == 503
            else:
                raise AssertionError("expected TrackerAPIError")

    async def test_non_retryable_status_fails_immediately(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-1",
                status=403,
                payload={"errorMessages": ["Forbidden"]},
            )

            try:
                await tracker_client.issue_get("TEST-1")
            except TrackerAPIError as exc:
                assert exc.status == 403
            else:
                raise AssertionError("expected TrackerAPIError")
