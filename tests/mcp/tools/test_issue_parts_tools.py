"""Tests for consolidated per-issue CRUD tools (issue_comments/links/worklogs/...)."""

from unittest.mock import AsyncMock

import pytest
from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.issues import (
    ChecklistItem,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    Worklog,
)
from tests.mcp.conftest import get_tool_result_content

# ─── issue_comments ────────────────────────────────────────────────


class TestIssueCommentsGet:
    async def test_returns_comments(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_comments: list[IssueComment],
    ) -> None:
        mock_issues_protocol.issue_get_comments.return_value = sample_comments

        result = await client_session.call_tool(
            "issue_comments", {"action": "get", "issue_id": "TEST-1"}
        )

        assert not result.isError
        mock_issues_protocol.issue_get_comments.assert_called_once()
        content = get_tool_result_content(result)
        assert content["comments"][0]["text"] == sample_comments[0].text

    async def test_restricted_queue(
        self,
        client_session_with_limits: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_comments", {"action": "get", "issue_id": "RESTRICTED-1"}
        )
        assert result.isError


class TestIssueCommentsAdd:
    async def test_adds_comment(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_comment: IssueComment,
    ) -> None:
        mock_issues_protocol.issue_add_comment.return_value = sample_comment

        result = await client_session.call_tool(
            "issue_comments",
            {
                "action": "add",
                "issue_id": "TEST-1",
                "text": "Hello",
                "summonees": ["user1"],
            },
        )

        assert not result.isError
        mock_issues_protocol.issue_add_comment.assert_called_once()
        call_kwargs = mock_issues_protocol.issue_add_comment.call_args.kwargs
        assert call_kwargs["text"] == "Hello"
        assert call_kwargs["summonees"] == ["user1"]
        content = get_tool_result_content(result)
        assert content["comment"]["id"] == sample_comment.id

    async def test_add_requires_text(
        self,
        client_session: ClientSession,
    ) -> None:
        result = await client_session.call_tool(
            "issue_comments", {"action": "add", "issue_id": "TEST-1"}
        )
        assert result.isError

    async def test_read_only_blocks_add(
        self,
        client_session_read_only: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "issue_comments",
            {"action": "add", "issue_id": "TEST-1", "text": "x"},
        )
        assert result.isError
        mock_issues_protocol.issue_add_comment.assert_not_called()


class TestIssueCommentsUpdate:
    async def test_updates_comment(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_comment: IssueComment,
    ) -> None:
        mock_issues_protocol.issue_update_comment.return_value = sample_comment

        result = await client_session.call_tool(
            "issue_comments",
            {
                "action": "update",
                "issue_id": "TEST-1",
                "comment_id": 10,
                "text": "Updated",
            },
        )

        assert not result.isError
        mock_issues_protocol.issue_update_comment.assert_called_once()
        content = get_tool_result_content(result)
        assert content["comment"]["id"] == sample_comment.id


class TestIssueCommentsDelete:
    async def test_deletes_comment(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        mock_issues_protocol.issue_delete_comment.return_value = None

        result = await client_session.call_tool(
            "issue_comments",
            {"action": "delete", "issue_id": "TEST-1", "comment_id": 10},
        )

        assert not result.isError
        mock_issues_protocol.issue_delete_comment.assert_called_once()
        content = get_tool_result_content(result)
        assert content == {"ok": True}


# ─── issue_links ────────────────────────────────────────────────


class TestIssueLinks:
    async def test_get(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_links: list[IssueLink],
    ) -> None:
        mock_issues_protocol.issues_get_links.return_value = sample_links

        result = await client_session.call_tool(
            "issue_links", {"action": "get", "issue_id": "TEST-1"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["links"][0]["direction"] == sample_links[0].direction

    async def test_add(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_link: IssueLink,
    ) -> None:
        mock_issues_protocol.issue_add_link.return_value = sample_link

        result = await client_session.call_tool(
            "issue_links",
            {
                "action": "add",
                "issue_id": "TEST-1",
                "relationship": "relates",
                "target_issue": "TEST-2",
            },
        )

        assert not result.isError
        mock_issues_protocol.issue_add_link.assert_called_once()
        content = get_tool_result_content(result)
        assert "link" in content

    async def test_delete(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        mock_issues_protocol.issue_delete_link.return_value = None

        result = await client_session.call_tool(
            "issue_links",
            {"action": "delete", "issue_id": "TEST-1", "link_id": 99},
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content == {"ok": True}


# ─── issue_worklogs ────────────────────────────────────────────────


class TestIssueWorklogs:
    async def test_get(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_worklogs: list[Worklog],
    ) -> None:
        mock_issues_protocol.issue_get_worklogs.return_value = sample_worklogs

        result = await client_session.call_tool(
            "issue_worklogs", {"action": "get", "issue_id": "TEST-1"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["worklogs"]) == len(sample_worklogs)

    async def test_add(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_worklog: Worklog,
    ) -> None:
        mock_issues_protocol.issue_add_worklog.return_value = sample_worklog

        result = await client_session.call_tool(
            "issue_worklogs",
            {"action": "add", "issue_id": "TEST-1", "duration": "PT1H"},
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issue_add_worklog.call_args.kwargs
        assert call_kwargs["duration"] == "PT1H"
        content = get_tool_result_content(result)
        assert content["worklog"]["id"] == sample_worklog.id

    async def test_update(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_worklog: Worklog,
    ) -> None:
        mock_issues_protocol.issue_update_worklog.return_value = sample_worklog

        result = await client_session.call_tool(
            "issue_worklogs",
            {
                "action": "update",
                "issue_id": "TEST-1",
                "worklog_id": 10,
                "duration": "PT2H",
            },
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issue_update_worklog.call_args.kwargs
        assert call_kwargs["duration"] == "PT2H"

    async def test_delete(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        mock_issues_protocol.issue_delete_worklog.return_value = None

        result = await client_session.call_tool(
            "issue_worklogs",
            {"action": "delete", "issue_id": "TEST-1", "worklog_id": 10},
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content == {"ok": True}


# ─── issue_attachments ────────────────────────────────────────────────


class TestIssueAttachments:
    async def test_get(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_attachments: list[IssueAttachment],
    ) -> None:
        mock_issues_protocol.issue_get_attachments.return_value = sample_attachments

        result = await client_session.call_tool(
            "issue_attachments", {"action": "get", "issue_id": "TEST-1"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["attachments"]) == len(sample_attachments)

    async def test_upload_base64(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_attachment: IssueAttachment,
    ) -> None:
        mock_issues_protocol.issue_upload_attachment.return_value = sample_attachment

        result = await client_session.call_tool(
            "issue_attachments",
            {
                "action": "upload",
                "issue_id": "TEST-1",
                "content_base64": "aGVsbG8=",
                "filename": "hello.txt",
            },
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issue_upload_attachment.call_args.kwargs
        assert call_kwargs["content_base64"] == "aGVsbG8="
        assert call_kwargs["filename"] == "hello.txt"
        content = get_tool_result_content(result)
        assert "attachment" in content

    async def test_download_base64(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        mock_issues_protocol.issue_download_attachment.return_value = {
            "content_base64": "aGVsbG8="
        }

        result = await client_session.call_tool(
            "issue_attachments",
            {
                "action": "download",
                "issue_id": "TEST-1",
                "attachment_id": "a1",
                "filename": "hello.txt",
                "return_base64": True,
            },
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["content_base64"] == "aGVsbG8="

    async def test_delete(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        mock_issues_protocol.issue_delete_attachment.return_value = None

        result = await client_session.call_tool(
            "issue_attachments",
            {"action": "delete", "issue_id": "TEST-1", "attachment_id": "a1"},
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content == {"ok": True}

    async def test_upload_source_url_disabled_by_default(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        # No allowlist configured in the default test session → source_url rejected.
        result = await client_session.call_tool(
            "issue_attachments",
            {
                "action": "upload",
                "issue_id": "TEST-1",
                "source_url": "https://files.example.com/f.pdf",
            },
        )
        assert result.isError
        mock_issues_protocol.issue_upload_attachment.assert_not_called()

    async def test_upload_requires_exactly_one_source(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session.call_tool(
            "issue_attachments",
            {
                "action": "upload",
                "issue_id": "TEST-1",
                "file_path": "/tmp/x",
                "content_base64": "aGVsbG8=",
            },
        )
        assert result.isError
        mock_issues_protocol.issue_upload_attachment.assert_not_called()


# ─── issue_checklist ────────────────────────────────────────────────


class TestIssueChecklist:
    async def test_get(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_checklist: list[ChecklistItem],
    ) -> None:
        mock_issues_protocol.issue_get_checklist.return_value = sample_checklist

        result = await client_session.call_tool(
            "issue_checklist", {"action": "get", "issue_id": "TEST-1"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["checklist"]) == len(sample_checklist)

    async def test_add(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_checklist: list[ChecklistItem],
    ) -> None:
        mock_issues_protocol.issue_add_checklist_item.return_value = sample_checklist

        result = await client_session.call_tool(
            "issue_checklist",
            {"action": "add", "issue_id": "TEST-1", "text": "New item"},
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issue_add_checklist_item.call_args.kwargs
        assert call_kwargs["text"] == "New item"

    async def test_update(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_checklist: list[ChecklistItem],
    ) -> None:
        mock_issues_protocol.issue_update_checklist_item.return_value = sample_checklist

        result = await client_session.call_tool(
            "issue_checklist",
            {
                "action": "update",
                "issue_id": "TEST-1",
                "item_id": "ci-1",
                "checked": True,
            },
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issue_update_checklist_item.call_args.kwargs
        assert call_kwargs["checked"] is True

    async def test_delete(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_checklist: list[ChecklistItem],
    ) -> None:
        mock_issues_protocol.issue_delete_checklist_item.return_value = sample_checklist

        result = await client_session.call_tool(
            "issue_checklist",
            {"action": "delete", "issue_id": "TEST-1", "item_id": "ci-1"},
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["ok"] is True
        assert len(content["remaining"]) == len(sample_checklist)

    async def test_clear(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        mock_issues_protocol.issue_clear_checklist.return_value = None

        result = await client_session.call_tool(
            "issue_checklist", {"action": "clear", "issue_id": "TEST-1"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content == {"ok": True}


# ─── issue_tags ────────────────────────────────────────────────


class TestIssueTags:
    @pytest.mark.parametrize("action", ["add", "remove"])
    async def test_tags(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
        action: str,
    ) -> None:
        mock = (
            mock_issues_protocol.issue_add_tags
            if action == "add"
            else mock_issues_protocol.issue_remove_tags
        )
        mock.return_value = sample_issue

        result = await client_session.call_tool(
            "issue_tags",
            {"action": action, "issue_id": "TEST-1", "tags": ["urgent"]},
        )

        assert not result.isError
        mock.assert_called_once()
        content = get_tool_result_content(result)
        assert content["issue"]["key"] == sample_issue.key

    async def test_read_only_blocks(
        self,
        client_session_read_only: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "issue_tags",
            {"action": "add", "issue_id": "TEST-1", "tags": ["x"]},
        )
        assert result.isError
        mock_issues_protocol.issue_add_tags.assert_not_called()
