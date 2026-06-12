"""Tests for transient-error retries on idempotent requests."""

from aiohttp import ClientPayloadError, ServerDisconnectedError
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


class TestTransientConnectionErrors:
    """Stale keep-alive connections die with payload/disconnect errors.

    The Tracker LB closes idle connections; the first request on a pooled
    connection then fails mid-flight. These must be retried for idempotent
    calls — including the POST-based search endpoints.
    """

    async def test_issues_find_retries_payload_error(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/_search?page=1&perPage=15",
                exception=ClientPayloadError("Response payload is not completed"),
            )
            m.post(
                "https://api.tracker.yandex.net/v3/issues/_search?page=1&perPage=15",
                payload=[{"key": "TEST-1", "summary": "Recovered"}],
            )

            result = await tracker_client.issues_find("Queue: TEST")

        assert result.issues[0].key == "TEST-1"

    async def test_issue_get_retries_server_disconnect(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-1",
                exception=ServerDisconnectedError(),
            )
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-1",
                payload={"key": "TEST-1", "summary": "Recovered"},
            )

            result = await tracker_client.issue_get("TEST-1")

        assert result.key == "TEST-1"

    async def test_issues_count_retries_payload_error(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/_count",
                exception=ClientPayloadError("Response payload is not completed"),
            )
            m.post(
                "https://api.tracker.yandex.net/v3/issues/_count",
                body="7",
            )

            result = await tracker_client.issues_count("Queue: TEST")

        assert result == 7

    async def test_payload_error_exhausts_retries(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            for _ in range(3):  # initial attempt + 2 retries
                m.post(
                    "https://api.tracker.yandex.net/v3/issues/_search?page=1&perPage=15",
                    exception=ClientPayloadError("truncated"),
                )

            try:
                await tracker_client.issues_find("Queue: TEST")
            except ClientPayloadError:
                pass
            else:
                raise AssertionError("expected ClientPayloadError")
