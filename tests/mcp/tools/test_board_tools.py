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


class TestBoardsGetAll:
    async def test_returns_boards(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_boards: list[Board],
    ) -> None:
        mock_boards_protocol.boards_list.return_value = sample_boards

        result = await client_session.call_tool("boards_get_all", {})

        assert not result.isError
        mock_boards_protocol.boards_list.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        items = content["boards"]
        assert len(items) == len(sample_boards)
        assert items[0]["name"] == "My Board"


class TestBoardGet:
    async def test_returns_board(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_board: Board,
    ) -> None:
        mock_boards_protocol.board_get.return_value = sample_board

        result = await client_session.call_tool("board_get", {"board_id": 73})

        assert not result.isError
        assert mock_boards_protocol.board_get.call_args.args[0] == 73
        content = get_tool_result_content(result)
        assert content["id"] == 73
        assert content["name"] == "My Board"


class TestBoardGetColumns:
    async def test_returns_columns(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_columns: list[BoardColumn],
    ) -> None:
        mock_boards_protocol.board_get_columns.return_value = sample_columns

        result = await client_session.call_tool("board_get_columns", {"board_id": 73})

        assert not result.isError
        assert mock_boards_protocol.board_get_columns.call_args.args[0] == 73
        content = get_tool_result_content(result)
        items = content["columns"]
        assert len(items) == 2
        assert items[0]["name"] == "Open"


class TestBoardGetSprints:
    async def test_returns_sprints(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_sprints: list[Sprint],
    ) -> None:
        mock_boards_protocol.board_get_sprints.return_value = sample_sprints

        result = await client_session.call_tool("board_get_sprints", {"board_id": 73})

        assert not result.isError
        content = get_tool_result_content(result)
        items = content["sprints"]
        assert len(items) == 2
        assert items[0]["status"] == "in_progress"
