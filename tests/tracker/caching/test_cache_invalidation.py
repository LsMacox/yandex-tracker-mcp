"""Tests for write-path cache invalidation and cache-key hygiene."""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from mcp_tracker.tracker.caching.client import (
    _auth_fingerprint,
    _build_key,
    make_cached_protocols,
)
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.issues import (
    ChecklistItem,
    Issue,
    IssueComment,
    IssueLink,
    IssueTransition,
    Worklog,
)
from mcp_tracker.tracker.proto.types.refs import IssueReference


class TestCacheKeyHygiene:
    def test_token_is_hashed_out_of_keys(self) -> None:
        auth = YandexAuth(token="super-secret-oauth-token")
        key = _build_key("issue_get", "TEST-1", auth=auth)
        assert "super-secret-oauth-token" not in key

    def test_different_tokens_produce_different_keys(self) -> None:
        key_a = _build_key("issue_get", "TEST-1", auth=YandexAuth(token="token-a"))
        key_b = _build_key("issue_get", "TEST-1", auth=YandexAuth(token="token-b"))
        assert key_a != key_b

    def test_same_identity_produces_same_key(self) -> None:
        key_a = _build_key("issue_get", "TEST-1", auth=YandexAuth(token="token-a"))
        key_b = _build_key("issue_get", "TEST-1", auth=YandexAuth(token="token-a"))
        assert key_a == key_b

    def test_none_auth_fingerprint_is_stable(self) -> None:
        assert _auth_fingerprint(None) == "-"


class TestWriteInvalidation:
    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        original = AsyncMock()
        original.issue_get.return_value = Issue(key="TEST-1", summary="Test Issue")
        original.issue_get_comments.return_value = [
            IssueComment(id=1, text="Test comment")
        ]
        original.issues_get_links.return_value = [
            IssueLink(
                id=1,
                object=IssueReference(id="TEST-2", key="TEST-2", display="Linked"),
            )
        ]
        original.issue_get_worklogs.return_value = [Worklog(id=1)]
        original.issue_get_checklist.return_value = [
            ChecklistItem(id="item-1", text="Item")
        ]
        original.issue_get_transitions.return_value = [
            IssueTransition(id="close", display="Close")
        ]
        original.issue_add_comment.return_value = IssueComment(id=2, text="New")
        original.issue_add_link.return_value = IssueLink(id=2)
        original.issue_update.return_value = Issue(key="TEST-1", summary="Updated")
        return original

    @pytest.fixture
    def caching_issues_protocol(self, mock_original: AsyncMock) -> Any:
        cache_collection = make_cached_protocols({"ttl": 300})
        return cache_collection.issues(mock_original)

    async def test_add_comment_invalidates_comments_cache(
        self, caching_issues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        await caching_issues_protocol.issue_get_comments("TEST-1")
        await caching_issues_protocol.issue_get_comments("TEST-1")
        assert mock_original.issue_get_comments.call_count == 1  # cache hit

        await caching_issues_protocol.issue_add_comment("TEST-1", text="hello")

        await caching_issues_protocol.issue_get_comments("TEST-1")
        assert mock_original.issue_get_comments.call_count == 2  # re-fetched

    async def test_add_link_invalidates_both_issues(
        self, caching_issues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        await caching_issues_protocol.issues_get_links("TEST-1")
        await caching_issues_protocol.issues_get_links("TEST-2")
        assert mock_original.issues_get_links.call_count == 2

        await caching_issues_protocol.issue_add_link(
            "TEST-1", relationship="relates", target_issue="TEST-2"
        )

        await caching_issues_protocol.issues_get_links("TEST-1")
        await caching_issues_protocol.issues_get_links("TEST-2")
        assert mock_original.issues_get_links.call_count == 4

    async def test_issue_update_invalidates_issue_get(
        self, caching_issues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        await caching_issues_protocol.issue_get("TEST-1")
        await caching_issues_protocol.issue_get("TEST-1")
        assert mock_original.issue_get.call_count == 1

        await caching_issues_protocol.issue_update("TEST-1", summary="Updated")

        await caching_issues_protocol.issue_get("TEST-1")
        assert mock_original.issue_get.call_count == 2

    async def test_invalidation_is_auth_scoped(
        self, caching_issues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        auth_a = YandexAuth(token="token-a")
        auth_b = YandexAuth(token="token-b")

        await caching_issues_protocol.issue_get_comments("TEST-1", auth=auth_a)
        await caching_issues_protocol.issue_get_comments("TEST-1", auth=auth_b)
        assert mock_original.issue_get_comments.call_count == 2

        # A's write only drops A's cached entry.
        await caching_issues_protocol.issue_add_comment(
            "TEST-1", text="hello", auth=auth_a
        )

        await caching_issues_protocol.issue_get_comments("TEST-1", auth=auth_a)
        assert mock_original.issue_get_comments.call_count == 3
        await caching_issues_protocol.issue_get_comments("TEST-1", auth=auth_b)
        assert mock_original.issue_get_comments.call_count == 3  # B still cached
