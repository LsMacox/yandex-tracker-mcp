"""Board and sprint MCP tools (read-only)."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.requests import Request

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.boards import (
    Board,
    BoardColumn,
    Sprint,
)

BoardID = Annotated[
    int,
    Field(description="Numeric Yandex Tracker board identifier, e.g. 42"),
]


def register_board_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register board/sprint read-only tools."""

    @mcp.tool(
        title="Get All Boards",
        description="List all agile task boards available in the organization. "
        "Returns a `{'boards': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def boards_get_all(
        ctx: Context[Any, AppContext, Request],
    ) -> dict[str, list[Board]]:
        items = await ctx.request_context.lifespan_context.boards.boards_list(
            auth=get_yandex_auth(ctx),
        )
        return {"boards": items}

    @mcp.tool(
        title="Get Board",
        description="Get full parameters of a specific agile board by its numeric identifier.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def board_get(
        ctx: Context[Any, AppContext, Request],
        board_id: BoardID,
    ) -> Board:
        return await ctx.request_context.lifespan_context.boards.board_get(
            board_id,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Get Board Columns",
        description="Get all columns of the specified agile board with their linked issue statuses. "
        "Returns a `{'columns': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def board_get_columns(
        ctx: Context[Any, AppContext, Request],
        board_id: BoardID,
    ) -> dict[str, list[BoardColumn]]:
        items = await ctx.request_context.lifespan_context.boards.board_get_columns(
            board_id,
            auth=get_yandex_auth(ctx),
        )
        return {"columns": items}

    @mcp.tool(
        title="Get Board Sprints",
        description=(
            "List all sprints (draft, in_progress, released, archived) of the given agile board. "
            "Returns a `{'sprints': [...]}` object. The `sprints` array is empty for boards "
            "without a sprint setup (kanban, filter-only, etc.)."
        ),
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def board_get_sprints(
        ctx: Context[Any, AppContext, Request],
        board_id: BoardID,
    ) -> dict[str, list[Sprint]]:
        items = await ctx.request_context.lifespan_context.boards.board_get_sprints(
            board_id,
            auth=get_yandex_auth(ctx),
        )
        return {"sprints": items}
