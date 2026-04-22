"""Issue read-only MCP tools."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import (
    IssueID,
    PageParam,
    PerPageParam,
    YTQuery,
)
from mcp_tracker.mcp.tools._access import check_issue_access
from mcp_tracker.mcp.utils import get_yandex_auth, set_non_needed_fields_null
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.issues import (
    Issue,
    IssueFieldsEnum,
    IssueTransition,
)


def register_issue_read_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register issue read-only tools."""

    @mcp.tool(
        title="Get Issue",
        description="Get a Yandex Tracker issue by its id",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        include_description: Annotated[
            bool,
            Field(
                description="Whether to include issue description in the issues result. "
                "It can be large, so use only when needed.",
            ),
        ] = True,
    ) -> Issue:
        check_issue_access(settings, issue_id)

        issue = await ctx.request_context.lifespan_context.issues.issue_get(
            issue_id,
            auth=get_yandex_auth(ctx),
        )

        if not include_description:
            issue.description = None

        return issue

    @mcp.tool(
        title="Find Issues",
        description=(
            "Find Yandex Tracker issues. Provide either a YQL `query` string OR a "
            "structured `filter` dict — not both.\n\n"
            "═══ YQL cheatsheet ═══\n"
            "Field names are PascalCase and case-sensitive:\n"
            "  • `Queue: TEST` — by queue key\n"
            '  • `Boards: "My Board"` — PLURAL, by board NAME (NOT `Board:`, NOT id)\n'
            "  • `Assignee: me()`, `Author: me()`, `Follower: me()`\n"
            "  • `Resolution: empty()` — open issues; `Resolution: notEmpty()` — closed\n"
            "  • `Status: open, inProgress` — OR-list of statuses\n"
            "  • `Type: bug, incident` — OR-list of issue types\n"
            "  • `Priority: critical, blocker`\n"
            "  • `Tags: urgent` / `Components: Core` / `Version: 1.2.0`\n"
            '  • `Sprint: "Sprint 1"` — by name\n'
            "  • `Created: > 2024-01-01` / `Updated: today() - 7d`\n"
            '  • `Summary: ~"keyword"` — contains; `Description: ~"..."`\n'
            "Combine with `AND`, `OR`, `NOT`; group with parentheses.\n"
            'Sort INSIDE the query: append `"Sort By": Updated DESC, Key ASC`.\n\n'
            "═══ `order` parameter ═══\n"
            "Use `['-updated_at', '+priority']` (prefix `-` DESC, `+`/none ASC).\n"
            'When combined with `query`, it\'s auto-folded into the `"Sort By"` clause.\n'
            "With `filter`, it's sent as-is in the body.\n\n"
            "═══ Standard enum keys ═══\n"
            "Status: `open, inProgress, needInfo, closed, resolved, reopened`.\n"
            "Type: `task, bug, feature, improvement, incident, epic`.\n"
            "Priority: `trivial, minor, normal, critical, blocker`.\n"
            "Resolution: `fixed, wontFix, cantReproduce, duplicate, later, dontDo`.\n\n"
            "To restrict to specific issue keys use `keys`."
        ),
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issues_find(
        ctx: Context[Any, AppContext],
        query: Annotated[
            str | None,
            Field(
                description="YQL query (see issues query docs). Mutually usable with filter."
            ),
        ] = None,
        filter: Annotated[
            dict[str, Any] | None,
            Field(
                description="Structured filter object; keys are field ids, values are scalars or lists."
            ),
        ] = None,
        order: Annotated[
            list[str] | None,
            Field(
                description="Sort by field keys; prefix with '+' / '-' for asc/desc, default ascending."
            ),
        ] = None,
        keys: Annotated[
            list[str] | None,
            Field(description="Restrict search to the given issue keys/ids."),
        ] = None,
        include_description: Annotated[
            bool,
            Field(
                description="Whether to include issue description in the issues result. It can be large, so use only when needed.",
            ),
        ] = False,
        fields: Annotated[
            list[IssueFieldsEnum] | None,
            Field(
                description="Fields to include in the response. In order to not pollute context window - select "
                "appropriate fields beforehand. Not specifying fields will return all available."
            ),
        ] = None,
        page: PageParam = 1,
        per_page: PerPageParam = 100,
    ) -> dict[str, list[Issue]]:
        if query is None and filter is None and not keys:
            raise ValueError(
                "Provide at least one of: query, filter, or keys — "
                "cannot search without any criteria."
            )

        issues = await ctx.request_context.lifespan_context.issues.issues_find(
            query=query,
            filter=filter,
            order=order,
            keys=keys,
            per_page=per_page,
            page=page,
            auth=get_yandex_auth(ctx),
        )

        if not include_description:
            for issue in issues:
                issue.description = None  # Clear description to save context

        if fields is not None:
            set_non_needed_fields_null(issues, {f.name for f in fields})

        return {"issues": issues}

    @mcp.tool(
        title="Count Issues",
        description=(
            "Get the count of Yandex Tracker issues matching a YQL query. "
            'Use `Boards: "Name"` (plural) to filter by board name; `Board` (singular) is not valid YQL.'
        ),
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issues_count(
        ctx: Context[Any, AppContext],
        query: YTQuery,
    ) -> int:
        return await ctx.request_context.lifespan_context.issues.issues_count(
            query,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Get Issue Transitions",
        description="Get possible status transitions for a Yandex Tracker issue. "
        "Returns a `{'transitions': [...]}` object.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get_transitions(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
    ) -> dict[str, list[IssueTransition]]:
        check_issue_access(settings, issue_id)

        items = await ctx.request_context.lifespan_context.issues.issue_get_transitions(
            issue_id,
            auth=get_yandex_auth(ctx),
        )
        return {"transitions": items}
