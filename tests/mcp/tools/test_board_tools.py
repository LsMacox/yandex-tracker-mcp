from unittest.mock import AsyncMock

import pytest
from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.boards import (
    Board,
    BoardColumn,
    BoardColumnStatus,
    BoardReference,
    Sprint,
)
from tests.mcp.conftest import get_tool_result_content


@pytest.fixture
def sample_board() -> Board:
    return Board.model_construct(
        id=73,
        name="My Board",
        version=1,
        columns=[
            BoardColumn.model_construct(
                id=1,
                name="Open",
                statuses=[
                    BoardColumnStatus.model_construct(
                        id="1", key="open", display="Open"
                    )
                ],
            )
        ],
    )


@pytest.fixture
def sample_boards(sample_board: Board) -> list[Board]:
    return [
        sample_board,
        Board.model_construct(id=74, name="Second Board"),
    ]


@pytest.fixture
def sample_columns() -> list[BoardColumn]:
    return [
        BoardColumn.model_construct(id=1, name="Open"),
        BoardColumn.model_construct(id=2, name="In Progress"),
    ]


@pytest.fixture
def sample_sprint() -> Sprint:
    return Sprint.model_construct(
        id=44,
        name="Sprint 1",
        status="in_progress",
        archived=False,
        board=BoardReference.model_construct(id=73, display="My Board"),
    )


@pytest.fixture
def sample_sprints(sample_sprint: Sprint) -> list[Sprint]:
    return [
        sample_sprint,
        Sprint.model_construct(id=45, name="Sprint 2", status="draft"),
    ]


class TestBoardsList:
    async def test_list(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_boards: list[Board],
    ) -> None:
        mock_boards_protocol.boards_list.return_value = sample_boards

        result = await client_session.call_tool("boards", {"action": "list"})

        assert not result.isError
        mock_boards_protocol.boards_list.assert_called_once()
        content = get_tool_result_content(result)
        items = content["boards"]
        assert len(items) == len(sample_boards)
        assert items[0]["name"] == "My Board"


class TestBoardsGet:
    async def test_get(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_board: Board,
    ) -> None:
        mock_boards_protocol.board_get.return_value = sample_board

        result = await client_session.call_tool(
            "boards", {"action": "get", "board_id": 73}
        )

        assert not result.isError
        assert mock_boards_protocol.board_get.call_args.args[0] == 73
        content = get_tool_result_content(result)
        assert content["board"]["id"] == 73


class TestBoardsColumns:
    async def test_columns(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_columns: list[BoardColumn],
    ) -> None:
        mock_boards_protocol.board_get_columns.return_value = sample_columns

        result = await client_session.call_tool(
            "boards", {"action": "columns", "board_id": 73}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        items = content["columns"]
        assert len(items) == 2


class TestBoardsSprints:
    async def test_sprints(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_sprints: list[Sprint],
    ) -> None:
        mock_boards_protocol.board_get_sprints.return_value = sample_sprints

        result = await client_session.call_tool(
            "boards", {"action": "sprints", "board_id": 73}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        items = content["sprints"]
        assert len(items) == 2


class TestBoardsCreate:
    async def test_create(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_board: Board,
    ) -> None:
        mock_boards_protocol.board_create.return_value = sample_board

        result = await client_session.call_tool(
            "boards",
            {
                "action": "create",
                "name": "My Board",
                "filter": {"queue": "TEST"},
            },
        )

        assert not result.isError
        call_kwargs = mock_boards_protocol.board_create.call_args.kwargs
        assert call_kwargs["name"] == "My Board"
        assert call_kwargs["filter"] == {"queue": "TEST"}


class TestBoardsDelete:
    async def test_delete(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        mock_boards_protocol.board_delete.return_value = None

        result = await client_session.call_tool(
            "boards", {"action": "delete", "board_id": 73}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content == {"ok": True}

    async def test_read_only_blocks(
        self,
        client_session_read_only: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "boards", {"action": "delete", "board_id": 73}
        )
        assert result.isError
        mock_boards_protocol.board_delete.assert_not_called()


class TestBoardColumns:
    async def test_create(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        mock_boards_protocol.board_column_create.return_value = (
            BoardColumn.model_construct(id=10, name="Blocked")
        )

        result = await client_session.call_tool(
            "board_columns",
            {
                "action": "create",
                "board_id": 73,
                "name": "Blocked",
                "statuses": ["blocked"],
            },
        )

        assert not result.isError
        call_kwargs = mock_boards_protocol.board_column_create.call_args.kwargs
        assert call_kwargs["name"] == "Blocked"
        assert call_kwargs["statuses"] == ["blocked"]

    async def test_update(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        mock_boards_protocol.board_column_update.return_value = (
            BoardColumn.model_construct(id=10, name="Renamed")
        )

        result = await client_session.call_tool(
            "board_columns",
            {
                "action": "update",
                "board_id": 73,
                "column_id": 10,
                "name": "Renamed",
            },
        )

        assert not result.isError

    async def test_delete(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        mock_boards_protocol.board_column_delete.return_value = None

        result = await client_session.call_tool(
            "board_columns",
            {"action": "delete", "board_id": 73, "column_id": 10},
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content == {"ok": True}
