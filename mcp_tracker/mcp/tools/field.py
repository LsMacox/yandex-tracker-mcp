"""Global field and metadata MCP tools (read-only)."""

from typing import Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import IssueID
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.fields import GlobalField
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.resolutions import Resolution
from mcp_tracker.tracker.proto.types.statuses import Status


def register_field_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register global field and metadata tools (all read-only).

    All list-returning tools wrap their result in a single-key dict so MCP
    clients receive one JSON object per response rather than a stream of
    concatenated objects (which some clients render as invalid JSON).
    """

    @mcp.tool(
        title="Get Global Fields",
        description="Get all global fields available in Yandex Tracker. "
        "Returns a `{'fields': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_global_fields(
        ctx: Context[Any, AppContext],
    ) -> dict[str, list[GlobalField]]:
        items = await ctx.request_context.lifespan_context.fields.get_global_fields(
            auth=get_yandex_auth(ctx),
        )
        return {"fields": items}

    @mcp.tool(
        title="Get Statuses",
        description="Get all statuses available in Yandex Tracker. "
        "Returns a `{'statuses': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_statuses(
        ctx: Context[Any, AppContext],
    ) -> dict[str, list[Status]]:
        items = await ctx.request_context.lifespan_context.fields.get_statuses(
            auth=get_yandex_auth(ctx),
        )
        return {"statuses": items}

    @mcp.tool(
        title="Get Issue Types",
        description="Get all issue types available in Yandex Tracker. "
        "Returns a `{'issue_types': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_issue_types(
        ctx: Context[Any, AppContext],
    ) -> dict[str, list[IssueType]]:
        items = await ctx.request_context.lifespan_context.fields.get_issue_types(
            auth=get_yandex_auth(ctx),
        )
        return {"issue_types": items}

    @mcp.tool(
        title="Get Priorities",
        description="Get all priorities available in Yandex Tracker. "
        "Returns a `{'priorities': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_priorities(
        ctx: Context[Any, AppContext],
    ) -> dict[str, list[Priority]]:
        items = await ctx.request_context.lifespan_context.fields.get_priorities(
            auth=get_yandex_auth(ctx),
        )
        return {"priorities": items}

    @mcp.tool(
        title="Get Resolutions",
        description="Get all resolutions available in Yandex Tracker. "
        "Returns a `{'resolutions': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_resolutions(
        ctx: Context[Any, AppContext],
    ) -> dict[str, list[Resolution]]:
        items = await ctx.request_context.lifespan_context.fields.get_resolutions(
            auth=get_yandex_auth(ctx),
        )
        return {"resolutions": items}

    @mcp.tool(
        title="Get Issue URL",
        description="Get a Yandex Tracker issue url by its id",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get_url(
        issue_id: IssueID,
    ) -> str:
        return f"https://tracker.yandex.ru/{issue_id}"
