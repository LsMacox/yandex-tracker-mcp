"""Dashboard MCP tools."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import PageParam, PerPageParam
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.misc import Dashboard, DashboardWidget

DashboardID = Annotated[str, Field(description="Dashboard identifier")]


def register_dashboard_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    @mcp.tool(
        title="List Dashboards",
        description="List dashboards accessible to the user. "
        "Returns a `{'dashboards': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def dashboards_list(
        ctx: Context[Any, AppContext],
        page: PageParam = 1,
        per_page: PerPageParam = 50,
    ) -> dict[str, list[Dashboard]]:
        items = await ctx.request_context.lifespan_context.dashboards.dashboards_list(
            per_page=per_page, page=page, auth=get_yandex_auth(ctx)
        )
        return {"dashboards": items}

    @mcp.tool(
        title="Get Dashboard",
        description="Get a dashboard by id.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def dashboard_get(
        ctx: Context[Any, AppContext], dashboard_id: DashboardID
    ) -> Dashboard:
        return await ctx.request_context.lifespan_context.dashboards.dashboard_get(
            dashboard_id, auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Get Dashboard Widgets",
        description="Get all widgets of the dashboard. "
        "Returns a `{'widgets': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def dashboard_get_widgets(
        ctx: Context[Any, AppContext], dashboard_id: DashboardID
    ) -> dict[str, list[DashboardWidget]]:
        items = (
            await ctx.request_context.lifespan_context.dashboards.dashboard_get_widgets(
                dashboard_id, auth=get_yandex_auth(ctx)
            )
        )
        return {"widgets": items}


def register_dashboard_write_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    @mcp.tool(
        title="Create Dashboard",
        description="Create a new dashboard.",
    )
    async def dashboard_create(
        ctx: Context[Any, AppContext],
        name: Annotated[str, Field(description="Dashboard name")],
        fields: Annotated[
            dict[str, Any] | None,
            Field(description="Additional dashboard fields (access, widgets, ...)"),
        ] = None,
    ) -> Dashboard:
        return await ctx.request_context.lifespan_context.dashboards.dashboard_create(
            name=name, fields=fields, auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Update Dashboard",
        description="Update dashboard (PATCH). Pass the current dashboard `version` "
        "to use optimistic locking (sent as If-Match header) — Tracker often requires it.",
    )
    async def dashboard_update(
        ctx: Context[Any, AppContext],
        dashboard_id: DashboardID,
        fields: Annotated[dict[str, Any], Field(description="Fields to update")],
        version: Annotated[
            str | int | None,
            Field(description="Current dashboard version for If-Match optimistic lock"),
        ] = None,
    ) -> Dashboard:
        return await ctx.request_context.lifespan_context.dashboards.dashboard_update(
            dashboard_id,
            fields=fields,
            version=version,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Dashboard",
        description="Delete a dashboard.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def dashboard_delete(
        ctx: Context[Any, AppContext], dashboard_id: DashboardID
    ) -> dict[str, bool]:
        await ctx.request_context.lifespan_context.dashboards.dashboard_delete(
            dashboard_id, auth=get_yandex_auth(ctx)
        )
        return {"ok": True}
