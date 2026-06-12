from typing import Any

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.types.issues import Issue, IssueSearchPage
from tests.aioresponses_utils import RequestCapture


class TestIssuesFind:
    async def test_success(
        self, tracker_client: TrackerClient, sample_issue_data: dict[str, Any]
    ) -> None:
        search_response = [sample_issue_data]

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/_search?page=1&perPage=15",
                payload=search_response,
            )

            result = await tracker_client.issues_find("Queue: TEST")

            assert isinstance(result, IssueSearchPage)
            assert len(result.issues) == 1
            assert isinstance(result.issues[0], Issue)
            assert result.issues[0].key == "TEST-123"

    async def test_with_pagination(
        self, tracker_client: TrackerClient, sample_issue_data: dict[str, Any]
    ) -> None:
        search_response = [sample_issue_data]
        capture = RequestCapture(payload=search_response)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/_search?page=2&perPage=50",
                callback=capture.callback,
            )

            result = await tracker_client.issues_find(
                "Queue: TEST", per_page=50, page=2
            )

            assert isinstance(result, IssueSearchPage)
            assert len(result.issues) == 1

        capture.assert_called_once()
        capture.last_request.assert_params({"perPage": 50, "page": 2})
        capture.last_request.assert_json_field("query", "Queue: TEST")

    async def test_total_headers_parsed(
        self, tracker_client: TrackerClient, sample_issue_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/_search?page=1&perPage=15",
                payload=[sample_issue_data],
                headers={"X-Total-Count": "120", "X-Total-Pages": "8"},
            )

            result = await tracker_client.issues_find("Queue: TEST")

        assert result.total_count == 120
        assert result.total_pages == 8

    async def test_keys_folded_into_query(
        self, tracker_client: TrackerClient, sample_issue_data: dict[str, Any]
    ) -> None:
        # The API rejects `keys` combined with `query` — keys must be folded
        # into the YQL expression instead.
        capture = RequestCapture(payload=[sample_issue_data])

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/_search?page=1&perPage=15",
                callback=capture.callback,
            )

            await tracker_client.issues_find("Queue: TEST", keys=["TEST-1", "TEST-2"])

        body = capture.last_request.get_json_body()
        assert "keys" not in body
        assert body["query"] == 'Key: "TEST-1", "TEST-2" AND (Queue: TEST)'

    async def test_keys_only_uses_body_param(
        self, tracker_client: TrackerClient, sample_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=[sample_issue_data])

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/_search?page=1&perPage=15",
                callback=capture.callback,
            )

            await tracker_client.issues_find(keys=["TEST-1"])

        body = capture.last_request.get_json_body()
        assert body == {"keys": ["TEST-1"]}
