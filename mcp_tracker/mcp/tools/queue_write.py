"""Queue write MCP tools."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.queues import Queue


def register_queue_write_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register queue write tools."""

    @mcp.tool(
        title="Create Queue",
        description=(
            "Create a new Yandex Tracker queue. All required parameters: "
            "`key` (UPPERCASE project key, e.g. 'SANDBOX'), `name`, `lead` (owner login), "
            "`default_type` (one of: task, bug, feature, improvement, incident, epic), "
            "`default_priority` (one of: trivial, minor, normal, critical, blocker). "
            "Use `extra` for less common fields: `description`, `allowExternalMailing`, "
            "`denyVoting`, `issueTypesConfig`, `workflowsConfig`, etc. "
            "Useful for spinning up a sandbox queue for integration testing."
        ),
    )
    async def queue_create(
        ctx: Context[Any, AppContext],
        key: Annotated[str, Field(description="UPPERCASE queue key, e.g. 'SANDBOX'")],
        name: Annotated[str, Field(description="Human-readable queue name")],
        lead: Annotated[str, Field(description="Queue owner login")],
        default_type: Annotated[
            str,
            Field(
                description="Default issue type key. Standard: task, bug, feature, "
                "improvement, incident, epic."
            ),
        ] = "task",
        default_priority: Annotated[
            str,
            Field(
                description="Default priority key. Standard: trivial, minor, normal, "
                "critical, blocker."
            ),
        ] = "normal",
        extra: Annotated[
            dict[str, Any] | None,
            Field(description="Additional queue fields to forward to the API"),
        ] = None,
    ) -> Queue:
        return await ctx.request_context.lifespan_context.queues.queue_create(
            key=key,
            name=name,
            lead=lead,
            default_type=default_type,
            default_priority=default_priority,
            extra=extra,
            auth=get_yandex_auth(ctx),
        )
