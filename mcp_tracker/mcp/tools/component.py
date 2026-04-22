"""Queue components MCP tools."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import PageParam, PerPageParam, QueueID
from mcp_tracker.mcp.tools._access import check_queue_access
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.misc import Component

ComponentID = Annotated[
    str | int,
    Field(description="Component identifier (numeric id from components_list)"),
]


def register_component_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    @mcp.tool(
        title="List Components",
        description="List queue components available in the organization. "
        "Returns a `{'components': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def components_list(
        ctx: Context[Any, AppContext],
        page: PageParam = 1,
        per_page: PerPageParam = 50,
    ) -> dict[str, list[Component]]:
        items = await ctx.request_context.lifespan_context.components.components_list(
            per_page=per_page, page=page, auth=get_yandex_auth(ctx)
        )
        return {"components": items}

    @mcp.tool(
        title="Get Component",
        description="Get component details by id.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def component_get(
        ctx: Context[Any, AppContext], component_id: ComponentID
    ) -> Component:
        return await ctx.request_context.lifespan_context.components.component_get(
            component_id, auth=get_yandex_auth(ctx)
        )


def register_component_write_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    @mcp.tool(
        title="Create Component",
        description="Create a new component in the given queue.",
    )
    async def component_create(
        ctx: Context[Any, AppContext],
        name: Annotated[str, Field(description="Component name")],
        queue: QueueID,
        description: Annotated[
            str | None, Field(description="Optional description")
        ] = None,
        lead: Annotated[
            str | None, Field(description="Optional component lead login")
        ] = None,
        assign_auto: Annotated[
            bool | None,
            Field(
                description="Auto-assign component lead to issues with this component"
            ),
        ] = None,
        extra: Annotated[
            dict[str, Any] | None, Field(description="Additional body fields")
        ] = None,
    ) -> Component:
        check_queue_access(settings, queue)
        return await ctx.request_context.lifespan_context.components.component_create(
            name=name,
            queue=queue,
            description=description,
            lead=lead,
            assign_auto=assign_auto,
            extra=extra,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Update Component",
        description="Update component fields (PATCH). Pass the current component `version` "
        "to use optimistic locking (sent as If-Match header). Tracker returns 428 "
        "Precondition Required when you omit it — fetch via `component_get` first.",
    )
    async def component_update(
        ctx: Context[Any, AppContext],
        component_id: ComponentID,
        fields: Annotated[dict[str, Any], Field(description="Fields to update")],
        version: Annotated[
            str | int | None,
            Field(description="Current component version for If-Match optimistic lock"),
        ] = None,
    ) -> Component:
        return await ctx.request_context.lifespan_context.components.component_update(
            component_id,
            fields=fields,
            version=version,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Component",
        description="Delete a component. If Tracker rejects with 428, pass the current "
        "`version` — same optimistic-lock rule as `component_update`.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def component_delete(
        ctx: Context[Any, AppContext],
        component_id: ComponentID,
        version: Annotated[
            str | int | None,
            Field(description="Current component version for If-Match optimistic lock"),
        ] = None,
    ) -> dict[str, bool]:
        await ctx.request_context.lifespan_context.components.component_delete(
            component_id, version=version, auth=get_yandex_auth(ctx)
        )
        return {"ok": True}
