"""Queue automations (triggers / autoactions / macros / workflows).

Each concept is exposed as a single action-based tool. Write actions are
rejected in read-only mode via `require_write_mode()`.
"""

from typing import Annotated, Any, Literal, TypeVar

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from pydantic import BaseModel, Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import QueueID
from mcp_tracker.mcp.tools._access import check_queue_access, require_write_mode
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings

TriggerAction = Literal["list", "get", "create", "update", "delete"]
AutoactionAction = Literal["list", "get", "create", "update", "delete"]
MacroAction = Literal["list", "get", "create", "update", "delete"]
WorkflowAction = Literal["list", "get_queue"]


_T = TypeVar("_T")


def _dump(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True)
    if isinstance(value, list):
        return [_dump(v) for v in value]
    return value


def _require(value: _T | None, name: str, action: str) -> _T:
    if value is None:
        raise ValueError(f"`{name}` is required for action `{action}`.")
    return value


def register_automation_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register consolidated automation tools."""

    # ─── triggers ────────────────────────────────────────────────
    @mcp.tool(
        title="Triggers",
        description=(
            "Manage queue triggers (event-driven automations).\n\n"
            "Actions:\n"
            "- `list` → `{triggers: [...]}`; requires `queue_id`\n"
            "- `get` → trigger; requires `queue_id` and `trigger_id`\n"
            "- `create` → trigger; requires `queue_id`, `name`, `actions`; "
            "optional `conditions`, `active`, `extra`\n"
            "- `update` → trigger; requires `queue_id`, `trigger_id`, `fields`\n"
            "- `delete` → `{ok: true}`; requires `queue_id` and `trigger_id`"
        ),
    )
    async def triggers(
        ctx: Context[Any, AppContext],
        action: TriggerAction,
        queue_id: QueueID,
        trigger_id: Annotated[
            str | int | None, Field(description="Trigger id (get/update/delete)")
        ] = None,
        name: Annotated[str | None, Field(description="Trigger name (create)")] = None,
        actions: Annotated[
            list[dict[str, Any]] | None,
            Field(description="Action objects executed when triggered (create)"),
        ] = None,
        conditions: Annotated[
            list[dict[str, Any]] | None,
            Field(description="Trigger conditions (create)"),
        ] = None,
        active: Annotated[
            bool | None, Field(description="Enable/disable (create)")
        ] = None,
        fields: Annotated[
            dict[str, Any] | None, Field(description="Fields to update (update)")
        ] = None,
        extra: Annotated[
            dict[str, Any] | None, Field(description="Extra body fields (create)")
        ] = None,
    ) -> dict[str, Any]:
        check_queue_access(settings, queue_id)
        automations = ctx.request_context.lifespan_context.automations
        auth = get_yandex_auth(ctx)

        def _need_id() -> str | int:
            if trigger_id is None:
                raise ValueError(f"`trigger_id` is required for action `{action}`.")
            return trigger_id

        if action == "list":
            items = await automations.triggers_list(queue_id, auth=auth)
            return {"triggers": _dump(items)}
        if action == "get":
            item = await automations.trigger_get(queue_id, _need_id(), auth=auth)
            return {"trigger": _dump(item)}

        require_write_mode(settings, action)

        if action == "create":
            name_ = _require(name, "name", action)
            actions_ = _require(actions, "actions", action)
            item = await automations.trigger_create(
                queue_id,
                name=name_,
                actions=actions_,
                conditions=conditions,
                active=active,
                extra=extra,
                auth=auth,
            )
            return {"trigger": _dump(item)}
        if action == "update":
            flds = _require(fields, "fields", action)
            item = await automations.trigger_update(
                queue_id, _need_id(), fields=flds, auth=auth
            )
            return {"trigger": _dump(item)}
        if action == "delete":
            await automations.trigger_delete(queue_id, _need_id(), auth=auth)
            return {"ok": True}
        raise ValueError(f"Unknown action: {action}")

    # ─── autoactions ────────────────────────────────────────────────
    @mcp.tool(
        title="Autoactions",
        description=(
            "Manage queue autoactions (scheduled automations: filter + cron + actions).\n\n"
            "Actions:\n"
            "- `list` → `{autoactions: [...]}`; requires `queue_id`\n"
            "- `get` → autoaction; requires `queue_id` and `autoaction_id`\n"
            "- `create` → autoaction; requires `queue_id`, `name`, `filter`, `actions`; "
            "optional `cron_expression`, `active`, `extra`\n"
            "- `update` → autoaction; requires `queue_id`, `autoaction_id`, `fields`\n"
            "- `delete` → `{ok: true}`; requires `queue_id` and `autoaction_id`"
        ),
    )
    async def autoactions(
        ctx: Context[Any, AppContext],
        action: AutoactionAction,
        queue_id: QueueID,
        autoaction_id: Annotated[
            str | int | None, Field(description="Autoaction id (get/update/delete)")
        ] = None,
        name: Annotated[
            str | None, Field(description="Autoaction name (create)")
        ] = None,
        filter: Annotated[
            dict[str, Any] | None,
            Field(description="Filter selecting target issues (create)"),
        ] = None,
        actions: Annotated[
            list[dict[str, Any]] | None,
            Field(description="Actions to execute (create)"),
        ] = None,
        cron_expression: Annotated[
            str | None, Field(description="Cron expression (create)")
        ] = None,
        active: Annotated[
            bool | None, Field(description="Enable flag (create)")
        ] = None,
        fields: Annotated[
            dict[str, Any] | None, Field(description="Fields to update (update)")
        ] = None,
        extra: Annotated[
            dict[str, Any] | None, Field(description="Extra body fields (create)")
        ] = None,
    ) -> dict[str, Any]:
        check_queue_access(settings, queue_id)
        automations = ctx.request_context.lifespan_context.automations
        auth = get_yandex_auth(ctx)

        def _need_id() -> str | int:
            if autoaction_id is None:
                raise ValueError(f"`autoaction_id` is required for action `{action}`.")
            return autoaction_id

        if action == "list":
            items = await automations.autoactions_list(queue_id, auth=auth)
            return {"autoactions": _dump(items)}
        if action == "get":
            item = await automations.autoaction_get(queue_id, _need_id(), auth=auth)
            return {"autoaction": _dump(item)}

        require_write_mode(settings, action)

        if action == "create":
            name_ = _require(name, "name", action)
            filter_ = _require(filter, "filter", action)
            actions_ = _require(actions, "actions", action)
            item = await automations.autoaction_create(
                queue_id,
                name=name_,
                filter=filter_,
                actions=actions_,
                cron_expression=cron_expression,
                active=active,
                extra=extra,
                auth=auth,
            )
            return {"autoaction": _dump(item)}
        if action == "update":
            flds = _require(fields, "fields", action)
            item = await automations.autoaction_update(
                queue_id, _need_id(), fields=flds, auth=auth
            )
            return {"autoaction": _dump(item)}
        if action == "delete":
            await automations.autoaction_delete(queue_id, _need_id(), auth=auth)
            return {"ok": True}
        raise ValueError(f"Unknown action: {action}")

    # ─── macros ────────────────────────────────────────────────
    @mcp.tool(
        title="Macros",
        description=(
            "Manage queue macros (comment templates + field changes).\n\n"
            "Actions:\n"
            "- `list` → `{macros: [...]}`; requires `queue_id`\n"
            "- `get` → macro; requires `queue_id` and `macro_id`\n"
            "- `create` → macro; requires `queue_id`, `name`; "
            "optional `body`, `field_changes`, `extra`\n"
            "- `update` → macro; requires `queue_id`, `macro_id`, `fields`\n"
            "- `delete` → `{ok: true}`; requires `queue_id` and `macro_id`"
        ),
    )
    async def macros(
        ctx: Context[Any, AppContext],
        action: MacroAction,
        queue_id: QueueID,
        macro_id: Annotated[
            str | int | None, Field(description="Macro id (get/update/delete)")
        ] = None,
        name: Annotated[str | None, Field(description="Macro name (create)")] = None,
        body: Annotated[
            str | None, Field(description="Comment template body (create)")
        ] = None,
        field_changes: Annotated[
            list[dict[str, Any]] | None,
            Field(description="Field change operations (create)"),
        ] = None,
        fields: Annotated[
            dict[str, Any] | None, Field(description="Fields to update (update)")
        ] = None,
        extra: Annotated[
            dict[str, Any] | None, Field(description="Extra body fields (create)")
        ] = None,
    ) -> dict[str, Any]:
        check_queue_access(settings, queue_id)
        automations = ctx.request_context.lifespan_context.automations
        auth = get_yandex_auth(ctx)

        def _need_id() -> str | int:
            if macro_id is None:
                raise ValueError(f"`macro_id` is required for action `{action}`.")
            return macro_id

        if action == "list":
            items = await automations.macros_list(queue_id, auth=auth)
            return {"macros": _dump(items)}
        if action == "get":
            item = await automations.macro_get(queue_id, _need_id(), auth=auth)
            return {"macro": _dump(item)}

        require_write_mode(settings, action)

        if action == "create":
            name_ = _require(name, "name", action)
            item = await automations.macro_create(
                queue_id,
                name=name_,
                body=body,
                field_changes=field_changes,
                extra=extra,
                auth=auth,
            )
            return {"macro": _dump(item)}
        if action == "update":
            flds = _require(fields, "fields", action)
            item = await automations.macro_update(
                queue_id, _need_id(), fields=flds, auth=auth
            )
            return {"macro": _dump(item)}
        if action == "delete":
            await automations.macro_delete(queue_id, _need_id(), auth=auth)
            return {"ok": True}
        raise ValueError(f"Unknown action: {action}")

    # ─── workflows ────────────────────────────────────────────────
    @mcp.tool(
        title="Workflows",
        description=(
            "Read organization and queue workflows (status graphs).\n\n"
            "Actions:\n"
            "- `list` → `{workflows: [...]}` — all workflows in the org\n"
            "- `get_queue` → workflow or null; requires `queue_id`"
        ),
    )
    async def workflows(
        ctx: Context[Any, AppContext],
        action: WorkflowAction,
        queue_id: Annotated[
            str | None, Field(description="Queue key (get_queue)")
        ] = None,
    ) -> dict[str, Any]:
        automations = ctx.request_context.lifespan_context.automations
        auth = get_yandex_auth(ctx)

        if action == "list":
            items = await automations.workflows_list(auth=auth)
            return {"workflows": _dump(items)}
        if action == "get_queue":
            qid = _require(queue_id, "queue_id", action)
            check_queue_access(settings, qid)
            item = await automations.queue_workflow_get(qid, auth=auth)
            return {"workflow": _dump(item) if item is not None else None}
        raise ValueError(f"Unknown action: {action}")
