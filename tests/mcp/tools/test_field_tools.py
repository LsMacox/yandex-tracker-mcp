from unittest.mock import AsyncMock

import pytest
from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.fields import GlobalField
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.resolutions import Resolution
from mcp_tracker.tracker.proto.types.statuses import Status
from tests.mcp.conftest import get_tool_result_content


class TestTrackerReference:
    async def test_global_fields(
        self,
        client_session: ClientSession,
        mock_fields_protocol: AsyncMock,
        sample_global_fields: list[GlobalField],
    ) -> None:
        mock_fields_protocol.get_global_fields.return_value = sample_global_fields

        result = await client_session.call_tool(
            "tracker_reference", {"kind": "global_fields"}
        )

        assert not result.isError
        mock_fields_protocol.get_global_fields.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        items = content["global_fields"]
        assert len(items) == len(sample_global_fields)
        assert items[0]["id"] == sample_global_fields[0].id
        assert items[0]["name"] == sample_global_fields[0].name

    async def test_statuses(
        self,
        client_session: ClientSession,
        mock_fields_protocol: AsyncMock,
        sample_statuses: list[Status],
    ) -> None:
        mock_fields_protocol.get_statuses.return_value = sample_statuses

        result = await client_session.call_tool(
            "tracker_reference", {"kind": "statuses"}
        )

        assert not result.isError
        mock_fields_protocol.get_statuses.assert_called_once()
        content = get_tool_result_content(result)
        items = content["statuses"]
        assert len(items) == len(sample_statuses)
        assert items[0]["key"] == sample_statuses[0].key
        assert items[0]["name"] == sample_statuses[0].name

    async def test_issue_types(
        self,
        client_session: ClientSession,
        mock_fields_protocol: AsyncMock,
        sample_issue_types: list[IssueType],
    ) -> None:
        mock_fields_protocol.get_issue_types.return_value = sample_issue_types

        result = await client_session.call_tool(
            "tracker_reference", {"kind": "issue_types"}
        )

        assert not result.isError
        mock_fields_protocol.get_issue_types.assert_called_once()
        content = get_tool_result_content(result)
        items = content["issue_types"]
        assert len(items) == len(sample_issue_types)
        assert items[0]["key"] == sample_issue_types[0].key
        assert items[0]["name"] == sample_issue_types[0].name

    async def test_priorities(
        self,
        client_session: ClientSession,
        mock_fields_protocol: AsyncMock,
        sample_priorities: list[Priority],
    ) -> None:
        mock_fields_protocol.get_priorities.return_value = sample_priorities

        result = await client_session.call_tool(
            "tracker_reference", {"kind": "priorities"}
        )

        assert not result.isError
        mock_fields_protocol.get_priorities.assert_called_once()
        content = get_tool_result_content(result)
        items = content["priorities"]
        assert len(items) == len(sample_priorities)
        assert items[0]["key"] == sample_priorities[0].key

    async def test_resolutions(
        self,
        client_session: ClientSession,
        mock_fields_protocol: AsyncMock,
        sample_resolutions: list[Resolution],
    ) -> None:
        mock_fields_protocol.get_resolutions.return_value = sample_resolutions

        result = await client_session.call_tool(
            "tracker_reference", {"kind": "resolutions"}
        )

        assert not result.isError
        mock_fields_protocol.get_resolutions.assert_called_once()
        content = get_tool_result_content(result)
        items = content["resolutions"]
        assert len(items) == len(sample_resolutions)
        assert items[0]["key"] == sample_resolutions[0].key

    @pytest.mark.parametrize(
        "kind,mock_attr,sample_fixture",
        [
            ("global_fields", "get_global_fields", "sample_global_fields"),
            ("statuses", "get_statuses", "sample_statuses"),
            ("issue_types", "get_issue_types", "sample_issue_types"),
            ("priorities", "get_priorities", "sample_priorities"),
            ("resolutions", "get_resolutions", "sample_resolutions"),
        ],
    )
    async def test_only_requested_kind_fetched(
        self,
        client_session: ClientSession,
        mock_fields_protocol: AsyncMock,
        request: pytest.FixtureRequest,
        kind: str,
        mock_attr: str,
        sample_fixture: str,
    ) -> None:
        sample = request.getfixturevalue(sample_fixture)
        getattr(mock_fields_protocol, mock_attr).return_value = sample

        result = await client_session.call_tool("tracker_reference", {"kind": kind})

        assert not result.isError
        # Only the requested kind's method is called; others remain untouched.
        for attr in [
            "get_global_fields",
            "get_statuses",
            "get_issue_types",
            "get_priorities",
            "get_resolutions",
        ]:
            if attr == mock_attr:
                getattr(mock_fields_protocol, attr).assert_called_once()
            else:
                getattr(mock_fields_protocol, attr).assert_not_called()

    async def test_invalid_kind_is_rejected(
        self,
        client_session: ClientSession,
    ) -> None:
        result = await client_session.call_tool(
            "tracker_reference", {"kind": "nonsense"}
        )
        assert result.isError
