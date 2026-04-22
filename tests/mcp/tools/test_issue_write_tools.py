from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.issues import Issue, IssueTransition
from tests.mcp.conftest import get_tool_result_content


class TestIssueExecuteTransition:
    async def test_executes_transition(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_transitions: list[IssueTransition],
    ) -> None:
        mock_issues_protocol.issue_execute_transition.return_value = sample_transitions

        result = await client_session.call_tool(
            "issue_execute_transition",
            {"issue_id": "TEST-123", "transition_id": "start_progress"},
        )

        assert not result.isError
        mock_issues_protocol.issue_execute_transition.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert content[0]["id"] == sample_transitions[0].id

    async def test_with_fields(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_transitions: list[IssueTransition],
    ) -> None:
        mock_issues_protocol.issue_execute_transition.return_value = sample_transitions

        result = await client_session.call_tool(
            "issue_execute_transition",
            {
                "issue_id": "TEST-123",
                "transition_id": "resolve",
                "fields": {"resolution": "fixed"},
            },
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issue_execute_transition.call_args.kwargs
        assert call_kwargs["fields"] == {"resolution": "fixed"}

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_execute_transition",
            {"issue_id": "RESTRICTED-123", "transition_id": "start_progress"},
        )

        assert result.isError
        mock_issues_protocol.issue_execute_transition.assert_not_called()


class TestIssueClose:
    async def test_closes_issue(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_transitions: list[IssueTransition],
    ) -> None:
        mock_issues_protocol.issue_close.return_value = sample_transitions

        result = await client_session.call_tool(
            "issue_close",
            {"issue_id": "TEST-123", "resolution_id": "fixed"},
        )

        assert not result.isError
        mock_issues_protocol.issue_close.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)


class TestIssueCreate:
    async def test_creates_issue(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
    ) -> None:
        mock_issues_protocol.issue_create.return_value = sample_issue

        result = await client_session.call_tool(
            "issue_create",
            {"queue": "TEST", "summary": "New test issue"},
        )

        assert not result.isError
        mock_issues_protocol.issue_create.assert_called_once()
        content = get_tool_result_content(result)
        assert content["key"] == sample_issue.key

    async def test_with_all_parameters(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
    ) -> None:
        mock_issues_protocol.issue_create.return_value = sample_issue

        result = await client_session.call_tool(
            "issue_create",
            {
                "queue": "TEST",
                "summary": "New test issue",
                "description": "Detailed description",
                "type": 1,
                "assignee": "user123",
                "priority": "normal",
            },
        )

        assert not result.isError
        mock_issues_protocol.issue_create.assert_called_once()

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_create",
            {"queue": "RESTRICTED", "summary": "New issue"},
        )

        assert result.isError
        mock_issues_protocol.issue_create.assert_not_called()


class TestIssueUpdate:
    async def test_updates_summary(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
    ) -> None:
        mock_issues_protocol.issue_update.return_value = sample_issue

        result = await client_session.call_tool(
            "issue_update",
            {"issue_id": "TEST-123", "summary": "Updated summary"},
        )

        assert not result.isError
        mock_issues_protocol.issue_update.assert_called_once()
        content = get_tool_result_content(result)
        assert content["key"] == sample_issue.key

    async def test_with_version_for_optimistic_locking(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
    ) -> None:
        mock_issues_protocol.issue_update.return_value = sample_issue

        result = await client_session.call_tool(
            "issue_update",
            {"issue_id": "TEST-123", "summary": "Updated summary", "version": 5},
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issue_update.call_args.kwargs
        assert call_kwargs["version"] == 5

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_update",
            {"issue_id": "RESTRICTED-123", "summary": "Updated summary"},
        )

        assert result.isError
        mock_issues_protocol.issue_update.assert_not_called()
