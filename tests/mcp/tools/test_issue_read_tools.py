from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.issues import Issue, IssueTransition
from tests.mcp.conftest import get_tool_result_content


class TestIssueGetUrl:
    async def test_returns_tracker_url(
        self,
        client_session: ClientSession,
    ) -> None:
        result = await client_session.call_tool(
            "issue_get_url", {"issue_id": "TEST-123"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content == "https://tracker.yandex.ru/TEST-123"


class TestIssueGet:
    async def test_returns_issue(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
    ) -> None:
        mock_issues_protocol.issue_get.return_value = sample_issue

        result = await client_session.call_tool("issue_get", {"issue_id": "TEST-123"})

        assert not result.isError
        mock_issues_protocol.issue_get.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        assert content["key"] == sample_issue.key
        assert content["summary"] == sample_issue.summary

    async def test_with_description_excluded(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
    ) -> None:
        mock_issues_protocol.issue_get.return_value = sample_issue

        result = await client_session.call_tool(
            "issue_get", {"issue_id": "TEST-123", "include_description": False}
        )

        assert not result.isError
        mock_issues_protocol.issue_get.assert_called_once()
        content = get_tool_result_content(result)
        assert content["key"] == sample_issue.key
        assert content.get("description") is None

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_get", {"issue_id": "RESTRICTED-123"}
        )

        assert result.isError
        mock_issues_protocol.issue_get.assert_not_called()


class TestIssuesFind:
    async def test_finds_issues(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issues: list[Issue],
    ) -> None:
        mock_issues_protocol.issues_find.return_value = sample_issues

        result = await client_session.call_tool("issues_find", {"query": "Queue: TEST"})

        assert not result.isError
        mock_issues_protocol.issues_find.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        items = content["issues"]
        assert len(items) == len(sample_issues)
        assert items[0]["key"] == sample_issues[0].key

    async def test_with_pagination(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issues: list[Issue],
    ) -> None:
        mock_issues_protocol.issues_find.return_value = sample_issues

        result = await client_session.call_tool(
            "issues_find", {"query": "Queue: TEST", "page": 2, "per_page": 50}
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issues_find.call_args.kwargs
        assert call_kwargs["page"] == 2
        assert call_kwargs["per_page"] == 50
        content = get_tool_result_content(result)
        assert len(content["issues"]) == len(sample_issues)

    async def test_excludes_description_by_default(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issues: list[Issue],
    ) -> None:
        mock_issues_protocol.issues_find.return_value = sample_issues

        result = await client_session.call_tool("issues_find", {"query": "Queue: TEST"})

        assert not result.isError
        mock_issues_protocol.issues_find.assert_called_once()
        content = get_tool_result_content(result)
        for issue in content["issues"]:
            assert issue.get("description") is None


class TestIssuesFindFilterToYql:
    async def test_filter_dict_converted_to_yql(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issues: list[Issue],
    ) -> None:
        mock_issues_protocol.issues_find.return_value = sample_issues

        result = await client_session.call_tool(
            "issues_find",
            {
                "filter": {
                    "queue": "TEST",
                    "resolution": "empty",
                    "assignee": "me",
                },
            },
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issues_find.call_args.kwargs
        assert call_kwargs["filter"] is None
        assert call_kwargs["query"] == (
            "Queue: TEST AND Resolution: empty() AND Assignee: me()"
        )

    async def test_filter_combined_with_query(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issues: list[Issue],
    ) -> None:
        mock_issues_protocol.issues_find.return_value = sample_issues

        result = await client_session.call_tool(
            "issues_find",
            {
                "query": "Tags: urgent",
                "filter": {"queue": "TEST"},
            },
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issues_find.call_args.kwargs
        assert call_kwargs["query"] == "(Tags: urgent) AND (Queue: TEST)"

    async def test_invalid_filter_returns_error(
        self,
        client_session: ClientSession,
    ) -> None:
        # Empty list for a field → can't render valid YQL.
        result = await client_session.call_tool(
            "issues_find",
            {"filter": {"status": []}},
        )
        assert result.isError


class TestIssuesCount:
    async def test_returns_count(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        mock_issues_protocol.issues_count.return_value = 42

        result = await client_session.call_tool(
            "issues_count", {"query": "Queue: TEST"}
        )

        assert not result.isError
        mock_issues_protocol.issues_count.assert_called_once()
        content = get_tool_result_content(result)
        assert content == 42


class TestIssueGetTransitions:
    async def test_returns_transitions(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_transitions: list[IssueTransition],
    ) -> None:
        mock_issues_protocol.issue_get_transitions.return_value = sample_transitions

        result = await client_session.call_tool(
            "issue_get_transitions", {"issue_id": "TEST-123"}
        )

        assert not result.isError
        mock_issues_protocol.issue_get_transitions.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        items = content["transitions"]
        assert len(items) == len(sample_transitions)
        assert items[0]["id"] == sample_transitions[0].id
