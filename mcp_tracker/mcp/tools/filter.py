"""Issue filter MCP tools (read + write)."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.misc import IssueFilter

FilterID = Annotated[str, Field(description="Saved filter identifier")]


def register_filter_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    @mcp.tool(
        title="List Issue Filters",
        description="List saved issue filters accessible to the user. "
        "Returns a `{'filters': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def filters_list(
        ctx: Context[Any, AppContext],
    ) -> dict[str, list[IssueFilter]]:
        items = await ctx.request_context.lifespan_context.filters.filters_list(
            auth=get_yandex_auth(ctx)
        )
        return {"filters": items}

    @mcp.tool(
        title="Get Issue Filter",
        description="Get a single saved filter by its identifier.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def filter_get(
        ctx: Context[Any, AppContext], filter_id: FilterID
    ) -> IssueFilter:
        return await ctx.request_context.lifespan_context.filters.filter_get(
            filter_id, auth=get_yandex_auth(ctx)
        )


def register_filter_write_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    @mcp.tool(
        title="Create Issue Filter",
        description="Create a saved YQL filter with a name.",
    )
    async def filter_create(
        ctx: Context[Any, AppContext],
        name: Annotated[str, Field(description="Filter display name")],
        query: Annotated[str, Field(description="YQL query string")],
        owner: Annotated[
            str | None,
            Field(description="Owner login or uid (default: current user)"),
        ] = None,
        extra: Annotated[
            dict[str, Any] | None,
            Field(description="Additional body fields to forward to the API"),
        ] = None,
    ) -> IssueFilter:
        return await ctx.request_context.lifespan_context.filters.filter_create(
            name=name,
            query=query,
            owner=owner,
            extra=extra,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Update Issue Filter",
        description="Update a saved filter with PATCH semantics.",
    )
    async def filter_update(
        ctx: Context[Any, AppContext],
        filter_id: FilterID,
        fields: Annotated[
            dict[str, Any], Field(description="Fields to update (name, query, ...)")
        ],
    ) -> IssueFilter:
        return await ctx.request_context.lifespan_context.filters.filter_update(
            filter_id, fields=fields, auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Delete Issue Filter",
        description="Delete a saved filter.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def filter_delete(
        ctx: Context[Any, AppContext], filter_id: FilterID
    ) -> dict[str, bool]:
        await ctx.request_context.lifespan_context.filters.filter_delete(
            filter_id, auth=get_yandex_auth(ctx)
        )
        return {"ok": True}
