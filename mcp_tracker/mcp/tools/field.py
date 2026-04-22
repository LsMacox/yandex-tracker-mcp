"""Global field and metadata MCP tools (read-only)."""

from typing import Any, Literal

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import IssueID
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings

ReferenceKind = Literal[
    "global_fields",
    "statuses",
    "issue_types",
    "priorities",
    "resolutions",
]


def register_field_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register global reference/metadata tools (all read-only)."""

    @mcp.tool(
        title="Get Tracker Reference",
        description=(
            "Get reference data (dictionaries) from Yandex Tracker. "
            "Pick a single `kind` per call. Returns a `{kind: [...]}` object. "
            "Kinds:\n"
            "- `global_fields` — custom global fields (id, name, schema, ...)\n"
            "- `statuses` — all statuses across workflows\n"
            "- `issue_types` — issue types (task, bug, epic, ...)\n"
            "- `priorities` — priority levels (trivial..blocker)\n"
            "- `resolutions` — resolution values (fixed, wontFix, duplicate, ...)\n\n"
            "Note: priorities and resolutions are largely standard across installations; "
            "call this tool only when you need the exact list for the current organization."
        ),
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def tracker_reference(
        ctx: Context[Any, AppContext],
        kind: ReferenceKind,
    ) -> dict[str, list[Any]]:
        fields = ctx.request_context.lifespan_context.fields
        auth = get_yandex_auth(ctx)

        if kind == "global_fields":
            return {"global_fields": list(await fields.get_global_fields(auth=auth))}
        if kind == "statuses":
            return {"statuses": list(await fields.get_statuses(auth=auth))}
        if kind == "issue_types":
            return {"issue_types": list(await fields.get_issue_types(auth=auth))}
        if kind == "priorities":
            return {"priorities": list(await fields.get_priorities(auth=auth))}
        if kind == "resolutions":
            return {"resolutions": list(await fields.get_resolutions(auth=auth))}
        raise ValueError(f"Unknown reference kind: {kind}")

    @mcp.tool(
        title="Get Issue URL",
        description="Get a Yandex Tracker issue url by its id",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get_url(
        issue_id: IssueID,
    ) -> str:
        return f"https://tracker.yandex.ru/{issue_id}"
