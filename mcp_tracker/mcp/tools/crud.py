"""Consolidated entity CRUD tools: components, filters, dashboards, sprints.

Each tool accepts an `action` parameter so clients only see one tool per concept.
Write actions are rejected in read-only mode via `require_write_mode()`.
"""

from typing import Annotated, Any, Literal, TypeVar

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from pydantic import BaseModel, Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import PageParam, PerPageParam, QueueID
from mcp_tracker.mcp.tools._access import check_queue_access, require_write_mode
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings

ComponentAction = Literal["list", "get", "create", "update", "delete"]
FilterAction = Literal["list", "get", "create", "update", "delete"]
DashboardAction = Literal["list", "get", "widgets", "create", "update", "delete"]
SprintAction = Literal["get", "create", "update", "delete", "start", "finish"]


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


def register_crud_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register consolidated CRUD tools for components/filters/dashboards/sprints."""

    # ─── components ────────────────────────────────────────────────
    @mcp.tool(
        title="Components",
        description=(
            "Manage queue components.\n\n"
            "Actions:\n"
            "- `list` → `{components: [...]}` — paginated list across org\n"
            "- `get` → component; requires `component_id`\n"
            "- `create` → component; requires `name` and `queue`; optional `description`, `lead`, `assign_auto`, `extra`\n"
            "- `update` → component; requires `component_id` and `fields`; auto-fetches `version` "
            "for If-Match if you don't pass it\n"
            "- `delete` → `{ok: true}`; requires `component_id`"
        ),
    )
    async def components(
        ctx: Context[Any, AppContext],
        action: ComponentAction,
        component_id: Annotated[
            str | int | None, Field(description="Component id (get/update/delete)")
        ] = None,
        name: Annotated[
            str | None, Field(description="Component name (create)")
        ] = None,
        queue: Annotated[
            QueueID | None, Field(description="Queue key (create)")
        ] = None,
        description: Annotated[
            str | None, Field(description="Component description (create)")
        ] = None,
        lead: Annotated[
            str | None, Field(description="Component lead login (create)")
        ] = None,
        assign_auto: Annotated[
            bool | None,
            Field(description="Auto-assign lead on matching issues (create)"),
        ] = None,
        fields: Annotated[
            dict[str, Any] | None, Field(description="Fields to update (update)")
        ] = None,
        version: Annotated[
            str | int | None,
            Field(description="Optimistic-lock version (update/delete)"),
        ] = None,
        extra: Annotated[
            dict[str, Any] | None, Field(description="Extra body fields (create)")
        ] = None,
        page: PageParam = 1,
        per_page: PerPageParam = 25,
    ) -> dict[str, Any]:
        components_proto = ctx.request_context.lifespan_context.components
        auth = get_yandex_auth(ctx)

        if action == "list":
            items = await components_proto.components_list(
                per_page=per_page, page=page, auth=auth
            )
            return {"components": _dump(items)}
        if action == "get":
            if component_id is None:
                raise ValueError(f"`component_id` is required for action `{action}`.")
            item = await components_proto.component_get(component_id, auth=auth)
            return {"component": _dump(item)}

        require_write_mode(settings, action)

        if action == "create":
            name_ = _require(name, "name", action)
            queue_ = _require(queue, "queue", action)
            check_queue_access(settings, queue_)
            item = await components_proto.component_create(
                name=name_,
                queue=queue_,
                description=description,
                lead=lead,
                assign_auto=assign_auto,
                extra=extra,
                auth=auth,
            )
            return {"component": _dump(item)}
        if action == "update":
            if component_id is None:
                raise ValueError(f"`component_id` is required for action `{action}`.")
            flds = _require(fields, "fields", action)
            if version is None:
                current = await components_proto.component_get(component_id, auth=auth)
                version = current.version
            item = await components_proto.component_update(
                component_id, fields=flds, version=version, auth=auth
            )
            return {"component": _dump(item)}
        if action == "delete":
            if component_id is None:
                raise ValueError(f"`component_id` is required for action `{action}`.")
            await components_proto.component_delete(
                component_id, version=version, auth=auth
            )
            return {"ok": True}
        raise ValueError(f"Unknown action: {action}")

    # ─── filters ────────────────────────────────────────────────
    @mcp.tool(
        title="Filters",
        description=(
            "Manage saved issue (YQL) filters.\n\n"
            "Actions:\n"
            "- `list` → `{filters: [...]}`\n"
            "- `get` → filter; requires `filter_id`\n"
            "- `create` → filter; requires `name` and `query` (YQL)\n"
            "- `update` → filter; requires `filter_id` and `fields`\n"
            "- `delete` → `{ok: true}`; requires `filter_id`"
        ),
    )
    async def filters(
        ctx: Context[Any, AppContext],
        action: FilterAction,
        filter_id: Annotated[
            str | None, Field(description="Filter id (get/update/delete)")
        ] = None,
        name: Annotated[
            str | None, Field(description="Filter display name (create)")
        ] = None,
        query: Annotated[str | None, Field(description="YQL query (create)")] = None,
        owner: Annotated[
            str | None, Field(description="Owner login or uid (create)")
        ] = None,
        fields: Annotated[
            dict[str, Any] | None, Field(description="Fields to update (update)")
        ] = None,
        extra: Annotated[
            dict[str, Any] | None, Field(description="Extra body fields (create)")
        ] = None,
    ) -> dict[str, Any]:
        filters_proto = ctx.request_context.lifespan_context.filters
        auth = get_yandex_auth(ctx)

        if action == "list":
            items = await filters_proto.filters_list(auth=auth)
            return {"filters": _dump(items)}
        if action == "get":
            fid = _require(filter_id, "filter_id", action)
            item = await filters_proto.filter_get(fid, auth=auth)
            return {"filter": _dump(item)}

        require_write_mode(settings, action)

        if action == "create":
            name_ = _require(name, "name", action)
            query_ = _require(query, "query", action)
            item = await filters_proto.filter_create(
                name=name_, query=query_, owner=owner, extra=extra, auth=auth
            )
            return {"filter": _dump(item)}
        if action == "update":
            fid = _require(filter_id, "filter_id", action)
            flds = _require(fields, "fields", action)
            item = await filters_proto.filter_update(fid, fields=flds, auth=auth)
            return {"filter": _dump(item)}
        if action == "delete":
            fid = _require(filter_id, "filter_id", action)
            await filters_proto.filter_delete(fid, auth=auth)
            return {"ok": True}
        raise ValueError(f"Unknown action: {action}")

    # ─── dashboards ────────────────────────────────────────────────
    @mcp.tool(
        title="Dashboards",
        description=(
            "Manage dashboards.\n\n"
            "Actions:\n"
            "- `list` → `{dashboards: [...]}`\n"
            "- `get` → dashboard; requires `dashboard_id`\n"
            "- `widgets` → `{widgets: [...]}`; requires `dashboard_id`\n"
            "- `create` → dashboard; requires `name`; optional `fields`\n"
            "- `update` → dashboard; requires `dashboard_id` and `fields`; "
            "pass `version` for If-Match optimistic lock\n"
            "- `delete` → `{ok: true}`; requires `dashboard_id`"
        ),
    )
    async def dashboards(
        ctx: Context[Any, AppContext],
        action: DashboardAction,
        dashboard_id: Annotated[
            str | None, Field(description="Dashboard id (get/widgets/update/delete)")
        ] = None,
        name: Annotated[
            str | None, Field(description="Dashboard name (create)")
        ] = None,
        fields: Annotated[
            dict[str, Any] | None,
            Field(description="Dashboard body fields (create/update)"),
        ] = None,
        version: Annotated[
            str | int | None,
            Field(description="Version for If-Match (update)"),
        ] = None,
        page: PageParam = 1,
        per_page: PerPageParam = 25,
    ) -> dict[str, Any]:
        dashboards_proto = ctx.request_context.lifespan_context.dashboards
        auth = get_yandex_auth(ctx)

        if action == "list":
            dashboards_items = await dashboards_proto.dashboards_list(
                per_page=per_page, page=page, auth=auth
            )
            return {"dashboards": _dump(dashboards_items)}
        if action == "get":
            did = _require(dashboard_id, "dashboard_id", action)
            item = await dashboards_proto.dashboard_get(did, auth=auth)
            return {"dashboard": _dump(item)}
        if action == "widgets":
            did = _require(dashboard_id, "dashboard_id", action)
            widgets = await dashboards_proto.dashboard_get_widgets(did, auth=auth)
            return {"widgets": _dump(widgets)}

        require_write_mode(settings, action)

        if action == "create":
            name_ = _require(name, "name", action)
            item = await dashboards_proto.dashboard_create(
                name=name_, fields=fields, auth=auth
            )
            return {"dashboard": _dump(item)}
        if action == "update":
            did = _require(dashboard_id, "dashboard_id", action)
            flds = _require(fields, "fields", action)
            item = await dashboards_proto.dashboard_update(
                did, fields=flds, version=version, auth=auth
            )
            return {"dashboard": _dump(item)}
        if action == "delete":
            did = _require(dashboard_id, "dashboard_id", action)
            await dashboards_proto.dashboard_delete(did, auth=auth)
            return {"ok": True}
        raise ValueError(f"Unknown action: {action}")

    # ─── sprints ────────────────────────────────────────────────
    @mcp.tool(
        title="Sprints",
        description=(
            "Manage sprints (lifecycle + CRUD).\n\n"
            "Actions:\n"
            "- `get` → sprint; requires `sprint_id`\n"
            "- `create` → sprint; requires `board_id` and `name`; "
            "optional `start_date`/`end_date` (YYYY-MM-DD) or `start_date_time`/`end_date_time` (ISO8601)\n"
            "- `update` → sprint; requires `sprint_id` and `fields`\n"
            "- `delete` → `{ok: true}`; requires `sprint_id`\n"
            "- `start` → sprint (draft → in_progress); requires `sprint_id`\n"
            "- `finish` → sprint (in_progress → closed/archived); requires `sprint_id`\n\n"
            "To list sprints on a board use `boards(action='sprints', ...)`."
        ),
    )
    async def sprints(
        ctx: Context[Any, AppContext],
        action: SprintAction,
        sprint_id: Annotated[
            str | int | None,
            Field(description="Sprint id (get/update/delete/start/finish)"),
        ] = None,
        board_id: Annotated[int | None, Field(description="Board id (create)")] = None,
        name: Annotated[str | None, Field(description="Sprint name (create)")] = None,
        start_date: Annotated[
            str | None, Field(description="YYYY-MM-DD (create)")
        ] = None,
        end_date: Annotated[
            str | None, Field(description="YYYY-MM-DD (create)")
        ] = None,
        start_date_time: Annotated[
            str | None, Field(description="ISO8601 (create)")
        ] = None,
        end_date_time: Annotated[
            str | None, Field(description="ISO8601 (create)")
        ] = None,
        fields: Annotated[
            dict[str, Any] | None, Field(description="Fields to update (update)")
        ] = None,
        extra: Annotated[
            dict[str, Any] | None, Field(description="Extra body fields (create)")
        ] = None,
    ) -> dict[str, Any]:
        boards_proto = ctx.request_context.lifespan_context.boards
        auth = get_yandex_auth(ctx)

        def _need_sprint_id() -> str | int:
            if sprint_id is None:
                raise ValueError(f"`sprint_id` is required for action `{action}`.")
            return sprint_id

        if action == "get":
            sprint = await boards_proto.sprint_get(str(_need_sprint_id()), auth=auth)
            return {"sprint": _dump(sprint)}

        require_write_mode(settings, action)

        if action == "create":
            bid = _require(board_id, "board_id", action)
            name_ = _require(name, "name", action)
            sprint = await boards_proto.sprint_create(
                bid,
                name=name_,
                start_date=start_date,
                end_date=end_date,
                start_date_time=start_date_time,
                end_date_time=end_date_time,
                extra=extra,
                auth=auth,
            )
            return {"sprint": _dump(sprint)}
        if action == "update":
            flds = _require(fields, "fields", action)
            sprint = await boards_proto.sprint_update(
                _need_sprint_id(), fields=flds, auth=auth
            )
            return {"sprint": _dump(sprint)}
        if action == "delete":
            await boards_proto.sprint_delete(_need_sprint_id(), auth=auth)
            return {"ok": True}
        if action == "start":
            sprint = await boards_proto.sprint_start(_need_sprint_id(), auth=auth)
            return {"sprint": _dump(sprint)}
        if action == "finish":
            sprint = await boards_proto.sprint_finish(_need_sprint_id(), auth=auth)
            return {"sprint": _dump(sprint)}
        raise ValueError(f"Unknown action: {action}")
