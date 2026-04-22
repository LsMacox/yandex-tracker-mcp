"""Queue automations: triggers, autoactions, macros, workflows."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import QueueID
from mcp_tracker.mcp.tools._access import check_queue_access
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.misc import (
    Autoaction,
    Macro,
    Trigger,
    Workflow,
)

TriggerID = Annotated[str | int, Field(description="Trigger identifier")]
AutoactionID = Annotated[str | int, Field(description="Autoaction identifier")]
MacroID = Annotated[str | int, Field(description="Macro identifier")]


def register_automation_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    # --- triggers read ---
    @mcp.tool(
        title="List Triggers",
        description="List automation triggers of the queue.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def triggers_list(
        ctx: Context[Any, AppContext], queue_id: QueueID
    ) -> list[Trigger]:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.automations.triggers_list(
            queue_id, auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Get Trigger",
        description="Get a single trigger by id.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def trigger_get(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        trigger_id: TriggerID,
    ) -> Trigger:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.automations.trigger_get(
            queue_id, trigger_id, auth=get_yandex_auth(ctx)
        )

    # --- autoactions read ---
    @mcp.tool(
        title="List Autoactions",
        description="List scheduled autoactions of the queue.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def autoactions_list(
        ctx: Context[Any, AppContext], queue_id: QueueID
    ) -> list[Autoaction]:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.automations.autoactions_list(
            queue_id, auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Get Autoaction",
        description="Get a single autoaction by id.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def autoaction_get(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        action_id: AutoactionID,
    ) -> Autoaction:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.automations.autoaction_get(
            queue_id, action_id, auth=get_yandex_auth(ctx)
        )

    # --- macros read ---
    @mcp.tool(
        title="List Macros",
        description="List macros of the queue.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def macros_list(
        ctx: Context[Any, AppContext], queue_id: QueueID
    ) -> list[Macro]:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.automations.macros_list(
            queue_id, auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Get Macro",
        description="Get a macro by id.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def macro_get(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        macro_id: MacroID,
    ) -> Macro:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.automations.macro_get(
            queue_id, macro_id, auth=get_yandex_auth(ctx)
        )

    # --- workflows read ---
    @mcp.tool(
        title="List Workflows",
        description="List all workflows available in the organization.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def workflows_list(ctx: Context[Any, AppContext]) -> list[Workflow]:
        return await ctx.request_context.lifespan_context.automations.workflows_list(
            auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Get Queue Workflow",
        description="Get the workflow (status graph) configured for a queue. "
        "Useful before creating issues to understand available transitions.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def queue_workflow_get(
        ctx: Context[Any, AppContext], queue_id: QueueID
    ) -> Workflow:
        check_queue_access(settings, queue_id)
        return (
            await ctx.request_context.lifespan_context.automations.queue_workflow_get(
                queue_id, auth=get_yandex_auth(ctx)
            )
        )


def register_automation_write_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    # triggers write
    @mcp.tool(
        title="Create Trigger",
        description="Create an automation trigger for the queue. "
        "`actions` is a list of action dicts; `conditions` is a list of condition dicts.",
    )
    async def trigger_create(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        name: Annotated[str, Field(description="Trigger name")],
        actions: Annotated[
            list[dict[str, Any]], Field(description="Actions executed when triggered")
        ],
        conditions: Annotated[
            list[dict[str, Any]] | None, Field(description="Optional conditions list")
        ] = None,
        active: Annotated[
            bool | None, Field(description="Enable/disable the trigger")
        ] = None,
        extra: Annotated[
            dict[str, Any] | None, Field(description="Additional body fields")
        ] = None,
    ) -> Trigger:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.automations.trigger_create(
            queue_id,
            name=name,
            actions=actions,
            conditions=conditions,
            active=active,
            extra=extra,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(title="Update Trigger", description="Update trigger (PATCH).")
    async def trigger_update(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        trigger_id: TriggerID,
        fields: Annotated[dict[str, Any], Field(description="Fields to update")],
    ) -> Trigger:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.automations.trigger_update(
            queue_id, trigger_id, fields=fields, auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Delete Trigger",
        description="Delete a queue trigger.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def trigger_delete(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        trigger_id: TriggerID,
    ) -> dict[str, bool]:
        check_queue_access(settings, queue_id)
        await ctx.request_context.lifespan_context.automations.trigger_delete(
            queue_id, trigger_id, auth=get_yandex_auth(ctx)
        )
        return {"ok": True}

    # autoactions write
    @mcp.tool(
        title="Create Autoaction",
        description="Create a scheduled autoaction (filter + actions + cron).",
    )
    async def autoaction_create(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        name: Annotated[str, Field(description="Autoaction name")],
        filter: Annotated[
            dict[str, Any], Field(description="Filter selecting target issues")
        ],
        actions: Annotated[
            list[dict[str, Any]], Field(description="Actions to execute")
        ],
        cron_expression: Annotated[
            str | None, Field(description="Cron expression for schedule")
        ] = None,
        active: Annotated[bool | None, Field(description="Enable flag")] = None,
        extra: Annotated[
            dict[str, Any] | None, Field(description="Additional body fields")
        ] = None,
    ) -> Autoaction:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.automations.autoaction_create(
            queue_id,
            name=name,
            filter=filter,
            actions=actions,
            cron_expression=cron_expression,
            active=active,
            extra=extra,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(title="Update Autoaction", description="Update autoaction (PATCH).")
    async def autoaction_update(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        action_id: AutoactionID,
        fields: Annotated[dict[str, Any], Field(description="Fields to update")],
    ) -> Autoaction:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.automations.autoaction_update(
            queue_id, action_id, fields=fields, auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Delete Autoaction",
        description="Delete an autoaction.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def autoaction_delete(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        action_id: AutoactionID,
    ) -> dict[str, bool]:
        check_queue_access(settings, queue_id)
        await ctx.request_context.lifespan_context.automations.autoaction_delete(
            queue_id, action_id, auth=get_yandex_auth(ctx)
        )
        return {"ok": True}

    # macros write
    @mcp.tool(
        title="Create Macro",
        description="Create a macro (comment template + field changes) for the queue.",
    )
    async def macro_create(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        name: Annotated[str, Field(description="Macro name")],
        body: Annotated[str | None, Field(description="Comment template body")] = None,
        field_changes: Annotated[
            list[dict[str, Any]] | None,
            Field(description="Field change operations applied by the macro"),
        ] = None,
        extra: Annotated[
            dict[str, Any] | None, Field(description="Additional body fields")
        ] = None,
    ) -> Macro:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.automations.macro_create(
            queue_id,
            name=name,
            body=body,
            field_changes=field_changes,
            extra=extra,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(title="Update Macro", description="Update macro (PATCH).")
    async def macro_update(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        macro_id: MacroID,
        fields: Annotated[dict[str, Any], Field(description="Fields to update")],
    ) -> Macro:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.automations.macro_update(
            queue_id, macro_id, fields=fields, auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Delete Macro",
        description="Delete a macro.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def macro_delete(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        macro_id: MacroID,
    ) -> dict[str, bool]:
        check_queue_access(settings, queue_id)
        await ctx.request_context.lifespan_context.automations.macro_delete(
            queue_id, macro_id, auth=get_yandex_auth(ctx)
        )
        return {"ok": True}
