from typing import Any
from unittest.mock import AsyncMock

import pytest

from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.boards import Board, BoardColumn, Sprint


class TestCachingBoardsProtocol:
    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        original = AsyncMock()
        original.boards_list.return_value = [Board(id=1, name="Board 1")]
        original.board_get.return_value = Board(id=1, name="Board 1")
        original.board_get_columns.return_value = [BoardColumn(id=1, name="Open")]
        original.board_get_sprints.return_value = [Sprint(id=10, name="Sprint 1")]
        original.sprint_get.return_value = Sprint(id=10, name="Sprint 1")
        return original

    @pytest.fixture
    def caching_boards(self, mock_original: AsyncMock) -> Any:
        cache_config = {"ttl": 300}
        return make_cached_protocols(cache_config).boards(mock_original)

    async def test_boards_list_delegates(
        self,
        caching_boards: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_boards.boards_list(auth=yandex_auth)
        mock_original.boards_list.assert_called_once_with(auth=yandex_auth)
        assert result == mock_original.boards_list.return_value

    async def test_board_get_delegates(
        self, caching_boards: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_boards.board_get(1)
        mock_original.board_get.assert_called_once_with(1, auth=None)
        assert result == mock_original.board_get.return_value

    async def test_board_get_columns_delegates(
        self, caching_boards: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_boards.board_get_columns(1)
        mock_original.board_get_columns.assert_called_once_with(1, auth=None)
        assert result == mock_original.board_get_columns.return_value

    async def test_board_get_sprints_delegates(
        self, caching_boards: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_boards.board_get_sprints(1)
        mock_original.board_get_sprints.assert_called_once_with(1, auth=None)
        assert result == mock_original.board_get_sprints.return_value

    async def test_sprint_get_delegates(
        self, caching_boards: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_boards.sprint_get("10")
        mock_original.sprint_get.assert_called_once_with("10", auth=None)
        assert result == mock_original.sprint_get.return_value
