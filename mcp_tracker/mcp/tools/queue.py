"""Consolidated queue tool (list/tags/versions/fields/metadata/create)."""

import asyncio
from typing import Annotated, Any, Literal, TypeVar

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from pydantic import BaseModel, Field
from starlette.requests import Request

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import PerPageParam
from mcp_tracker.mcp.tools._access import check_queue_access, require_write_mode
from mcp_tracker.mcp.utils import get_yandex_auth, set_non_needed_fields_null
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.queues import (
    QueueExpandOption,
    QueueFieldsEnum,
)

QueueAction = Literal["list", "tags", "versions", "fields", "metadata", "create"]


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


def register_queue_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register consolidated queues tool."""

    @mcp.tool(
        title="Queues",
        description=(
            "Manage and inspect queues (Tracker projects).\n\n"
            "Actions:\n"
            "- `list` → `{queues: [...]}` — all queues available to the user; "
            "accepts `fields` to trim response, `page`/`per_page` for pagination "
            "(if `page` omitted — fetches everything)\n"
            "- `tags` → `{tags: [...]}`; requires `queue_id`\n"
            "- `versions` → `{versions: [...]}`; requires `queue_id`\n"
            "- `fields` → `{fields: [...]}`; requires `queue_id`; set "
            "`include_local_fields=False` to skip queue-specific fields\n"
            "- `metadata` → queue object; requires `queue_id`; pass `expand` to "
            "include e.g. `['issueTypesConfig']` for resolutions per type\n"
            "- `create` → queue; requires `key`, `name`, `lead`; `default_type` and "
            "`default_priority` default to `task`/`normal`"
        ),
    )
    async def queues(
        ctx: Context[Any, AppContext, Request],
        action: QueueAction,
        queue_id: Annotated[
            str | None, Field(description="Queue key (tags/versions/fields/metadata)")
        ] = None,
        fields: Annotated[
            list[QueueFieldsEnum] | None,
            Field(description="Fields to include in list response"),
        ] = None,
        page: Annotated[
            int | None,
            Field(description="Page number; None = fetch all (list action)"),
        ] = None,
        per_page: PerPageParam = 100,
        include_local_fields: Annotated[
            bool,
            Field(description="Include queue-local fields (fields action)"),
        ] = True,
        expand: Annotated[
            list[QueueExpandOption] | None,
            Field(description="Expand metadata sections (metadata action)"),
        ] = None,
        # create-only
        key: Annotated[
            str | None, Field(description="UPPERCASE queue key (create)")
        ] = None,
        name: Annotated[str | None, Field(description="Queue name (create)")] = None,
        lead: Annotated[str | None, Field(description="Owner login (create)")] = None,
        default_type: Annotated[
            str, Field(description="Default issue type key (create)")
        ] = "task",
        default_priority: Annotated[
            str, Field(description="Default priority key (create)")
        ] = "normal",
        extra: Annotated[
            dict[str, Any] | None, Field(description="Extra body fields (create)")
        ] = None,
    ) -> dict[str, Any]:
        queues_proto = ctx.request_context.lifespan_context.queues
        auth = get_yandex_auth(ctx)

        if action == "list":
            result = []
            fetch_all = page is None
            current = 1 if page is None else page
            while True:
                batch = await queues_proto.queues_list(
                    per_page=per_page, page=current, auth=auth
                )
                if not batch:
                    break
                if settings.tracker_limit_queues:
                    batch = [
                        q for q in batch if q.key in set(settings.tracker_limit_queues)
                    ]
                result.extend(batch)
                if not fetch_all:
                    break
                current += 1
            if fields is not None:
                set_non_needed_fields_null(result, {f.name for f in fields})
            return {"queues": _dump(result)}

        if action == "tags":
            qid = _require(queue_id, "queue_id", action)
            check_queue_access(settings, qid)
            tags = await queues_proto.queues_get_tags(qid, auth=auth)
            return {"tags": list(tags)}
        if action == "versions":
            qid = _require(queue_id, "queue_id", action)
            check_queue_access(settings, qid)
            items = await queues_proto.queues_get_versions(qid, auth=auth)
            return {"versions": _dump(items)}
        if action == "fields":
            qid = _require(queue_id, "queue_id", action)
            check_queue_access(settings, qid)
            if not include_local_fields:
                global_items = await queues_proto.queues_get_fields(qid, auth=auth)
                return {"fields": _dump(global_items)}
            async with asyncio.TaskGroup() as tg:
                global_task = tg.create_task(
                    queues_proto.queues_get_fields(qid, auth=auth)
                )
                local_task = tg.create_task(
                    queues_proto.queues_get_local_fields(qid, auth=auth)
                )
            return {"fields": _dump(global_task.result() + local_task.result())}
        if action == "metadata":
            qid = _require(queue_id, "queue_id", action)
            check_queue_access(settings, qid)
            item = await queues_proto.queue_get(qid, expand=expand, auth=auth)
            return {"queue": _dump(item)}

        require_write_mode(settings, action)

        if action == "create":
            key_ = _require(key, "key", action)
            name_ = _require(name, "name", action)
            lead_ = _require(lead, "lead", action)
            item = await queues_proto.queue_create(
                key=key_,
                name=name_,
                lead=lead_,
                default_type=default_type,
                default_priority=default_priority,
                extra=extra,
                auth=auth,
            )
            return {"queue": _dump(item)}
        raise ValueError(f"Unknown action: {action}")
