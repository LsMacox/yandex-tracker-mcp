"""Tests for consolidated bulk tool."""

from unittest.mock import AsyncMock

import pytest
from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.misc import BulkChangeResult
from tests.mcp.conftest import get_tool_result_content


@pytest.fixture
def sample_bulk_result() -> BulkChangeResult:
    return BulkChangeResult.model_construct(id="op-1", status="IN_PROGRESS")


class TestBulkUpdate:
    async def test_update(
        self,
        client_session: ClientSession,
        mock_bulkchange_protocol: AsyncMock,
        sample_bulk_result: BulkChangeResult,
    ) -> None:
        mock_bulkchange_protocol.bulk_update.return_value = sample_bulk_result

        result = await client_session.call_tool(
            "bulk",
            {
                "action": "update",
                "issues": ["TEST-1", "TEST-2"],
                "values": {"priority": "normal"},
            },
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["operation"]["id"] == sample_bulk_result.id


class TestBulkMove:
    async def test_move(
        self,
        client_session: ClientSession,
        mock_bulkchange_protocol: AsyncMock,
        sample_bulk_result: BulkChangeResult,
    ) -> None:
        mock_bulkchange_protocol.bulk_move.return_value = sample_bulk_result

        result = await client_session.call_tool(
            "bulk",
            {
                "action": "move",
                "issues": ["TEST-1"],
                "queue": "OTHER",
            },
        )

        assert not result.isError


class TestBulkTransition:
    async def test_transition(
        self,
        client_session: ClientSession,
        mock_bulkchange_protocol: AsyncMock,
        sample_bulk_result: BulkChangeResult,
    ) -> None:
        mock_bulkchange_protocol.bulk_transition.return_value = sample_bulk_result

        result = await client_session.call_tool(
            "bulk",
            {
                "action": "transition",
                "issues": ["TEST-1"],
                "transition": "closedMeta",
                "resolution": "fixed",
            },
        )

        assert not result.isError


class TestBulkStatus:
    async def test_status(
        self,
        client_session: ClientSession,
        mock_bulkchange_protocol: AsyncMock,
        sample_bulk_result: BulkChangeResult,
    ) -> None:
        mock_bulkchange_protocol.bulk_status_get.return_value = sample_bulk_result

        result = await client_session.call_tool(
            "bulk", {"action": "status", "operation_id": "op-1"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["operation"]["id"] == sample_bulk_result.id


class TestBulkReadOnly:
    async def test_update_blocked(
        self,
        client_session_read_only: ClientSession,
        mock_bulkchange_protocol: AsyncMock,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "bulk",
            {
                "action": "update",
                "issues": ["TEST-1"],
                "values": {"x": 1},
            },
        )
        assert result.isError
        mock_bulkchange_protocol.bulk_update.assert_not_called()
