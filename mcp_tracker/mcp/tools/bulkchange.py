"""Bulk change MCP tools."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import IssueIDs, QueueID
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.misc import BulkChangeResult


def register_bulkchange_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    @mcp.tool(
        title="Bulk Update Issues",
        description="Apply a single set of field values to many issues at once. "
        "Returns an operation descriptor; poll with bulk_status_get to see progress.",
    )
    async def bulk_update(
        ctx: Context[Any, AppContext],
        issues: IssueIDs,
        values: Annotated[
            dict[str, Any],
            Field(
                description="Field values to set on every issue (same shape as issue_update body)"
            ),
        ],
        comment: Annotated[str | None, Field(description="Comment to add")] = None,
        notify: Annotated[bool | None, Field(description="Send notifications")] = None,
    ) -> BulkChangeResult:
        return await ctx.request_context.lifespan_context.bulkchange.bulk_update(
            issues=issues,
            values=values,
            comment=comment,
            notify=notify,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Bulk Move Issues",
        description="Move many issues to another queue in a single bulk operation.",
    )
    async def bulk_move(
        ctx: Context[Any, AppContext],
        issues: IssueIDs,
        queue: QueueID,
        move_all_fields: Annotated[
            bool | None, Field(description="Preserve all fields during move")
        ] = None,
        initial_status: Annotated[
            bool | None, Field(description="Use initial status of target queue")
        ] = None,
        notify: Annotated[bool | None, Field(description="Send notifications")] = None,
        extra: Annotated[
            dict[str, Any] | None, Field(description="Additional body fields")
        ] = None,
    ) -> BulkChangeResult:
        return await ctx.request_context.lifespan_context.bulkchange.bulk_move(
            issues=issues,
            queue=queue,
            move_all_fields=move_all_fields,
            initial_status=initial_status,
            notify=notify,
            extra=extra,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Bulk Transition Issues",
        description="Execute the same status transition across many issues.",
    )
    async def bulk_transition(
        ctx: Context[Any, AppContext],
        issues: IssueIDs,
        transition: Annotated[str, Field(description="Transition id to execute")],
        comment: Annotated[str | None, Field(description="Comment to add")] = None,
        resolution: Annotated[
            str | None, Field(description="Resolution for 'done' transitions")
        ] = None,
        fields: Annotated[
            dict[str, Any] | None,
            Field(description="Extra field values required by the transition"),
        ] = None,
    ) -> BulkChangeResult:
        return await ctx.request_context.lifespan_context.bulkchange.bulk_transition(
            issues=issues,
            transition=transition,
            comment=comment,
            resolution=resolution,
            fields=fields,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Get Bulk Operation Status",
        description="Get progress of a bulk operation started by bulk_update/_move/_transition.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def bulk_status_get(
        ctx: Context[Any, AppContext],
        operation_id: Annotated[str, Field(description="Bulk operation id")],
    ) -> BulkChangeResult:
        return await ctx.request_context.lifespan_context.bulkchange.bulk_status_get(
            operation_id, auth=get_yandex_auth(ctx)
        )
