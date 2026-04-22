"""Projects, portfolios and goals MCP tools (new entities API)."""

from typing import Annotated, Any, Literal

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import PageParam, PerPageParam
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.misc import (
    Goal,
    Portfolio,
    Project,
    ProjectLegacy,
)

EntityType = Literal["project", "portfolio", "goal"]


def register_project_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    @mcp.tool(
        title="Search Projects",
        description="Search projects via the new entities API. "
        "Returns a `{'projects': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def projects_search(
        ctx: Context[Any, AppContext],
        filter: Annotated[
            dict[str, Any] | None,
            Field(description="Optional filter (status, lead, queue etc.)"),
        ] = None,
        order: Annotated[
            list[str] | None, Field(description="Sort keys, '-' prefix for DESC")
        ] = None,
        page: PageParam = 1,
        per_page: PerPageParam = 25,
    ) -> dict[str, list[Project]]:
        items = await ctx.request_context.lifespan_context.entities.projects_search(
            filter=filter,
            order=order,
            per_page=per_page,
            page=page,
            auth=get_yandex_auth(ctx),
        )
        return {"projects": items}

    @mcp.tool(
        title="Search Portfolios",
        description="Search portfolios via the new entities API. "
        "Returns a `{'portfolios': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def portfolios_search(
        ctx: Context[Any, AppContext],
        filter: Annotated[dict[str, Any] | None, Field(description="Filter")] = None,
        order: Annotated[list[str] | None, Field(description="Sort")] = None,
        page: PageParam = 1,
        per_page: PerPageParam = 25,
    ) -> dict[str, list[Portfolio]]:
        items = await ctx.request_context.lifespan_context.entities.portfolios_search(
            filter=filter,
            order=order,
            per_page=per_page,
            page=page,
            auth=get_yandex_auth(ctx),
        )
        return {"portfolios": items}

    @mcp.tool(
        title="Search Goals",
        description="Search OKR-style goals via the new entities API. "
        "Returns a `{'goals': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def goals_search(
        ctx: Context[Any, AppContext],
        filter: Annotated[dict[str, Any] | None, Field(description="Filter")] = None,
        order: Annotated[list[str] | None, Field(description="Sort")] = None,
        page: PageParam = 1,
        per_page: PerPageParam = 25,
    ) -> dict[str, list[Goal]]:
        items = await ctx.request_context.lifespan_context.entities.goals_search(
            filter=filter,
            order=order,
            per_page=per_page,
            page=page,
            auth=get_yandex_auth(ctx),
        )
        return {"goals": items}

    @mcp.tool(
        title="Get Entity",
        description="Get a single entity (project/portfolio/goal) by id. "
        "Returns the raw JSON body — shape depends on entity type.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def entity_get(
        ctx: Context[Any, AppContext],
        entity_type: Annotated[EntityType, Field(description="Entity type")],
        entity_id: Annotated[str, Field(description="Entity id")],
        fields: Annotated[
            list[str] | None, Field(description="Fields to include in response")
        ] = None,
        expand: Annotated[list[str] | None, Field(description="Expand options")] = None,
    ) -> dict[str, Any]:
        return await ctx.request_context.lifespan_context.entities.entity_get(
            entity_type,
            entity_id,
            fields=fields,
            expand=expand,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="List Legacy Projects",
        description="List legacy (/v2/projects) project entities. "
        "Returns a `{'projects': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def projects_legacy_list(
        ctx: Context[Any, AppContext],
        page: PageParam = 1,
        per_page: PerPageParam = 25,
    ) -> dict[str, list[ProjectLegacy]]:
        items = (
            await ctx.request_context.lifespan_context.entities.projects_legacy_list(
                per_page=per_page, page=page, auth=get_yandex_auth(ctx)
            )
        )
        return {"projects": items}


def register_project_write_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    @mcp.tool(
        title="Create Entity",
        description="Create a project, portfolio or goal. `fields` is a dict of entity fields "
        "(e.g. summary, description, lead, start, end, queues, status).",
    )
    async def entity_create(
        ctx: Context[Any, AppContext],
        entity_type: Annotated[EntityType, Field(description="Entity type")],
        fields: Annotated[
            dict[str, Any],
            Field(description="Entity field values (depends on entity type)"),
        ],
    ) -> dict[str, Any]:
        return await ctx.request_context.lifespan_context.entities.entity_create(
            entity_type, fields=fields, auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Update Entity",
        description="Update an entity with PATCH semantics.",
    )
    async def entity_update(
        ctx: Context[Any, AppContext],
        entity_type: Annotated[EntityType, Field(description="Entity type")],
        entity_id: Annotated[str, Field(description="Entity id")],
        fields: Annotated[dict[str, Any], Field(description="Fields to update")],
    ) -> dict[str, Any]:
        return await ctx.request_context.lifespan_context.entities.entity_update(
            entity_type, entity_id, fields=fields, auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Delete Entity",
        description="Delete an entity (project/portfolio/goal).",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def entity_delete(
        ctx: Context[Any, AppContext],
        entity_type: Annotated[EntityType, Field(description="Entity type")],
        entity_id: Annotated[str, Field(description="Entity id")],
    ) -> dict[str, bool]:
        await ctx.request_context.lifespan_context.entities.entity_delete(
            entity_type, entity_id, auth=get_yandex_auth(ctx)
        )
        return {"ok": True}
