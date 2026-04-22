"""Board/column/sprint write MCP tools."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.requests import Request

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.tools.board import BoardID
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.boards import Board, BoardColumn, Sprint

ColumnID = Annotated[int, Field(description="Numeric column identifier")]


def register_board_write_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register write tools for boards/columns/sprints."""

    @mcp.tool(
        title="Create Board",
        description="Create a new agile task board. "
        "Required: name. Typically also provide filter (queue/assignee) and column layout "
        "via nonParametrizedColumns (list of {name, statuses:[key,...]}).",
    )
    async def board_create(
        ctx: Context[Any, AppContext, Request],
        name: Annotated[str, Field(description="Board name")],
        filter: Annotated[
            dict[str, Any] | None,
            Field(description='Filter definition, e.g. {"queue": "TEST"}'),
        ] = None,
        non_parametrized_columns: Annotated[
            list[dict[str, Any]] | None,
            Field(
                description='Board columns as list of {"name": str, "statuses": [status_key,...]}'
            ),
        ] = None,
        columns: Annotated[
            list[dict[str, Any]] | None,
            Field(description="Alternative column payload (see Yandex docs)"),
        ] = None,
        query: Annotated[
            str | None, Field(description="YQL query to limit board issues")
        ] = None,
        order_by: Annotated[
            str | None, Field(description="Field key to order issues by")
        ] = None,
        order_asc: Annotated[
            bool | None, Field(description="Ascending order flag")
        ] = None,
        use_ranking: Annotated[
            bool | None, Field(description="Use ranking for issue order")
        ] = None,
        estimate_by: Annotated[
            str | None,
            Field(description="Field key to use for estimation (story_points etc.)"),
        ] = None,
        flow: Annotated[
            str | None, Field(description="Board flow id (kanban, scrum)")
        ] = None,
        extra: Annotated[
            dict[str, Any] | None,
            Field(description="Any additional body fields to forward to the API"),
        ] = None,
    ) -> Board:
        return await ctx.request_context.lifespan_context.boards.board_create(
            name=name,
            filter=filter,
            non_parametrized_columns=non_parametrized_columns,
            columns=columns,
            query=query,
            order_by=order_by,
            order_asc=order_asc,
            use_ranking=use_ranking,
            estimate_by=estimate_by,
            flow=flow,
            extra=extra,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Update Board",
        description="Update board parameters. Pass only fields to change via `fields` dict "
        "(name, nonParametrizedColumns, filter, query, orderBy, orderAsc, useRanking, estimateBy).",
    )
    async def board_update(
        ctx: Context[Any, AppContext, Request],
        board_id: BoardID,
        fields: Annotated[
            dict[str, Any],
            Field(description="JSON body with fields to update (PATCH semantics)"),
        ],
    ) -> Board:
        return await ctx.request_context.lifespan_context.boards.board_update(
            board_id,
            fields=fields,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Board",
        description="Delete an agile task board by its numeric identifier.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def board_delete(
        ctx: Context[Any, AppContext, Request],
        board_id: BoardID,
    ) -> dict[str, bool]:
        await ctx.request_context.lifespan_context.boards.board_delete(
            board_id,
            auth=get_yandex_auth(ctx),
        )
        return {"ok": True}

    @mcp.tool(
        title="Create Board Column",
        description="Add a new column to the given board. Columns group issue statuses.",
    )
    async def board_column_create(
        ctx: Context[Any, AppContext, Request],
        board_id: BoardID,
        name: Annotated[str, Field(description="Column name")],
        statuses: Annotated[
            list[str],
            Field(description="List of issue status keys that belong to this column"),
        ],
        version: Annotated[
            str | int | None,
            Field(description="Current board version for If-Match optimistic lock"),
        ] = None,
    ) -> BoardColumn:
        return await ctx.request_context.lifespan_context.boards.board_column_create(
            board_id,
            name=name,
            statuses=statuses,
            version=version,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Update Board Column",
        description="Update name and/or status set of an existing board column.",
    )
    async def board_column_update(
        ctx: Context[Any, AppContext, Request],
        board_id: BoardID,
        column_id: ColumnID,
        name: Annotated[str | None, Field(description="New column name")] = None,
        statuses: Annotated[
            list[str] | None, Field(description="Replacement list of status keys")
        ] = None,
        version: Annotated[
            str | int | None,
            Field(description="Current board version for If-Match optimistic lock"),
        ] = None,
    ) -> BoardColumn:
        return await ctx.request_context.lifespan_context.boards.board_column_update(
            board_id,
            column_id,
            name=name,
            statuses=statuses,
            version=version,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Board Column",
        description="Delete a column from the board.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def board_column_delete(
        ctx: Context[Any, AppContext, Request],
        board_id: BoardID,
        column_id: ColumnID,
        version: Annotated[
            str | int | None,
            Field(description="Current board version for If-Match optimistic lock"),
        ] = None,
    ) -> dict[str, bool]:
        await ctx.request_context.lifespan_context.boards.board_column_delete(
            board_id,
            column_id,
            version=version,
            auth=get_yandex_auth(ctx),
        )
        return {"ok": True}

    @mcp.tool(
        title="Update Sprint",
        description="Update sprint fields (name, dates, status) via PATCH. "
        "Pass only fields to change in `fields`.",
    )
    async def sprint_update(
        ctx: Context[Any, AppContext, Request],
        sprint_id: Annotated[
            str | int, Field(description="Sprint identifier from board_get_sprints")
        ],
        fields: Annotated[
            dict[str, Any],
            Field(
                description="JSON body with fields to update "
                "(name, startDate, endDate, startDateTime, endDateTime)."
            ),
        ],
    ) -> Sprint:
        return await ctx.request_context.lifespan_context.boards.sprint_update(
            sprint_id,
            fields=fields,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Sprint",
        description="Delete a sprint. Archiving is done via `sprint_finish` — this "
        "removes the sprint entirely.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def sprint_delete(
        ctx: Context[Any, AppContext, Request],
        sprint_id: Annotated[str | int, Field(description="Sprint identifier")],
    ) -> dict[str, bool]:
        await ctx.request_context.lifespan_context.boards.sprint_delete(
            sprint_id,
            auth=get_yandex_auth(ctx),
        )
        return {"ok": True}

    @mcp.tool(
        title="Start Sprint",
        description="Move a draft sprint to in_progress state.",
    )
    async def sprint_start(
        ctx: Context[Any, AppContext, Request],
        sprint_id: Annotated[str | int, Field(description="Sprint identifier")],
    ) -> Sprint:
        return await ctx.request_context.lifespan_context.boards.sprint_start(
            sprint_id, auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Finish Sprint",
        description="Finish (close / archive) an in_progress sprint. "
        "This is the closest equivalent to 'archive a sprint' in the Tracker API.",
    )
    async def sprint_finish(
        ctx: Context[Any, AppContext, Request],
        sprint_id: Annotated[str | int, Field(description="Sprint identifier")],
    ) -> Sprint:
        return await ctx.request_context.lifespan_context.boards.sprint_finish(
            sprint_id, auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Create Sprint",
        description="Create a new sprint on the given board. "
        "Dates are ISO strings (startDate/endDate as YYYY-MM-DD).",
    )
    async def sprint_create(
        ctx: Context[Any, AppContext, Request],
        board_id: BoardID,
        name: Annotated[str, Field(description="Sprint name")],
        start_date: Annotated[
            str | None, Field(description="Start date YYYY-MM-DD")
        ] = None,
        end_date: Annotated[
            str | None, Field(description="End date YYYY-MM-DD")
        ] = None,
        start_date_time: Annotated[
            str | None, Field(description="Full start datetime ISO8601")
        ] = None,
        end_date_time: Annotated[
            str | None, Field(description="Full end datetime ISO8601")
        ] = None,
        extra: Annotated[
            dict[str, Any] | None,
            Field(description="Any additional body fields to forward to the API"),
        ] = None,
    ) -> Sprint:
        return await ctx.request_context.lifespan_context.boards.sprint_create(
            board_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
            extra=extra,
            auth=get_yandex_auth(ctx),
        )
