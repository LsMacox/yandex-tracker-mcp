"""Extra write tools for issues: links, checklist, attachments, tags, move."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import IssueID, QueueID
from mcp_tracker.mcp.tools._access import check_issue_access, check_queue_access
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.issues import (
    ChecklistItem,
    Issue,
    IssueAttachment,
    IssueLink,
)


def register_issue_extras_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register write tools for issue links/checklist/attachments/tags/move."""

    @mcp.tool(
        title="Add Issue Link",
        description="Create a link from one issue to another. "
        "relationship is one of: relates, depends on, is dependent by, duplicates, "
        "is duplicated by, is epic of, has epic, is parent task for, is subtask for, etc.",
    )
    async def issue_add_link(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        relationship: Annotated[str, Field(description="Link relationship string")],
        target_issue: Annotated[
            str, Field(description="Target issue key (e.g. PROJ-2)")
        ],
    ) -> IssueLink:
        check_issue_access(settings, issue_id)
        return await ctx.request_context.lifespan_context.issues.issue_add_link(
            issue_id,
            relationship=relationship,
            target_issue=target_issue,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Issue Link",
        description="Remove a link from the issue by its link id.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def issue_delete_link(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        link_id: Annotated[int, Field(description="Numeric link identifier")],
    ) -> dict[str, bool]:
        check_issue_access(settings, issue_id)
        await ctx.request_context.lifespan_context.issues.issue_delete_link(
            issue_id, link_id, auth=get_yandex_auth(ctx)
        )
        return {"ok": True}

    @mcp.tool(
        title="Add Checklist Item",
        description="Append a new item to the issue checklist.",
    )
    async def issue_add_checklist_item(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        text: Annotated[str, Field(description="Checklist item text")],
        checked: Annotated[
            bool | None, Field(description="Initial checked state")
        ] = None,
        assignee: Annotated[
            str | int | None,
            Field(description="Optional assignee login or uid"),
        ] = None,
        deadline: Annotated[
            dict[str, Any] | None,
            Field(description="Deadline object {date, deadlineType, isExceeded?}"),
        ] = None,
    ) -> dict[str, list[ChecklistItem]]:
        check_issue_access(settings, issue_id)
        items = (
            await ctx.request_context.lifespan_context.issues.issue_add_checklist_item(
                issue_id,
                text=text,
                checked=checked,
                assignee=assignee,
                deadline=deadline,
                auth=get_yandex_auth(ctx),
            )
        )
        return {"checklist": items}

    @mcp.tool(
        title="Update Checklist Item",
        description="Update text, checked state, assignee or deadline of a checklist item.",
    )
    async def issue_update_checklist_item(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        item_id: Annotated[str, Field(description="Checklist item identifier")],
        text: Annotated[str | None, Field(description="New item text")] = None,
        checked: Annotated[bool | None, Field(description="New checked state")] = None,
        assignee: Annotated[
            str | int | None,
            Field(description="New assignee login or uid"),
        ] = None,
        deadline: Annotated[
            dict[str, Any] | None, Field(description="Deadline object")
        ] = None,
    ) -> dict[str, list[ChecklistItem]]:
        check_issue_access(settings, issue_id)
        items = await ctx.request_context.lifespan_context.issues.issue_update_checklist_item(
            issue_id,
            item_id,
            text=text,
            checked=checked,
            assignee=assignee,
            deadline=deadline,
            auth=get_yandex_auth(ctx),
        )
        return {"checklist": items}

    @mcp.tool(
        title="Delete Checklist Item",
        description="Remove a single checklist item from the issue.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def issue_delete_checklist_item(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        item_id: Annotated[str, Field(description="Checklist item identifier")],
    ) -> dict[str, Any]:
        check_issue_access(settings, issue_id)
        remaining = await ctx.request_context.lifespan_context.issues.issue_delete_checklist_item(
            issue_id, item_id, auth=get_yandex_auth(ctx)
        )
        return {
            "ok": True,
            "remaining": [item.model_dump() for item in remaining] if remaining else [],
        }

    @mcp.tool(
        title="Clear Issue Checklist",
        description="Delete all checklist items from the issue.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def issue_clear_checklist(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
    ) -> dict[str, bool]:
        check_issue_access(settings, issue_id)
        await ctx.request_context.lifespan_context.issues.issue_clear_checklist(
            issue_id, auth=get_yandex_auth(ctx)
        )
        return {"ok": True}

    @mcp.tool(
        title="Upload Issue Attachment",
        description=(
            "Upload a local file as an attachment to the issue. "
            "`file_path` MUST reference a file on the FILESYSTEM OF THE MCP SERVER "
            "itself — not on the MCP client machine. Uploading files from a "
            "remote client environment is not supported; copy the file onto the "
            "server host first."
        ),
    )
    async def issue_upload_attachment(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        file_path: Annotated[
            str,
            Field(
                description="Absolute or relative path to the file on the MCP server "
                "host (NOT on the client side)."
            ),
        ],
        filename: Annotated[
            str | None,
            Field(
                description="Override filename shown in Tracker (defaults to basename)"
            ),
        ] = None,
    ) -> IssueAttachment:
        check_issue_access(settings, issue_id)
        return (
            await ctx.request_context.lifespan_context.issues.issue_upload_attachment(
                issue_id,
                file_path=file_path,
                filename=filename,
                auth=get_yandex_auth(ctx),
            )
        )

    @mcp.tool(
        title="Delete Issue Attachment",
        description="Remove an attachment from the issue.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def issue_delete_attachment(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        attachment_id: Annotated[str, Field(description="Attachment id")],
    ) -> dict[str, bool]:
        check_issue_access(settings, issue_id)
        await ctx.request_context.lifespan_context.issues.issue_delete_attachment(
            issue_id, attachment_id, auth=get_yandex_auth(ctx)
        )
        return {"ok": True}

    @mcp.tool(
        title="Download Issue Attachment",
        description="Download an attachment file and save it locally. "
        "Returns the final path on disk. dest_path may be a directory "
        "(saves with original filename) or a full file path.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_download_attachment(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        attachment_id: Annotated[str, Field(description="Attachment id")],
        filename: Annotated[str, Field(description="Attachment filename in Tracker")],
        dest_path: Annotated[
            str,
            Field(
                description="Destination path (directory or full file path) on this machine"
            ),
        ],
    ) -> dict[str, str]:
        check_issue_access(settings, issue_id)
        path = (
            await ctx.request_context.lifespan_context.issues.issue_download_attachment(
                issue_id,
                attachment_id,
                filename,
                dest_path=dest_path,
                auth=get_yandex_auth(ctx),
            )
        )
        return {"path": path}

    @mcp.tool(
        title="Add Issue Tags",
        description="Append tags to the issue without removing existing ones.",
    )
    async def issue_add_tags(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        tags: Annotated[list[str], Field(description="Tags to add")],
    ) -> Issue:
        check_issue_access(settings, issue_id)
        return await ctx.request_context.lifespan_context.issues.issue_add_tags(
            issue_id, tags, auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Remove Issue Tags",
        description="Remove specific tags from the issue.",
    )
    async def issue_remove_tags(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        tags: Annotated[list[str], Field(description="Tags to remove")],
    ) -> Issue:
        check_issue_access(settings, issue_id)
        return await ctx.request_context.lifespan_context.issues.issue_remove_tags(
            issue_id, tags, auth=get_yandex_auth(ctx)
        )

    @mcp.tool(
        title="Move Issue to Queue",
        description="Move an issue to another queue. Optionally preserve all fields "
        "or set the initial status of the target queue.",
    )
    async def issue_move_to_queue(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        queue: QueueID,
        move_all_fields: Annotated[
            bool | None,
            Field(description="Keep all fields including queue-specific ones"),
        ] = None,
        initial_status: Annotated[
            bool | None, Field(description="Set target queue initial status")
        ] = None,
        notify: Annotated[bool | None, Field(description="Send notifications")] = None,
        expand: Annotated[
            list[str] | None, Field(description="Expand fields in response")
        ] = None,
        extra: Annotated[
            dict[str, Any] | None,
            Field(description="Additional body fields to override per move"),
        ] = None,
    ) -> Issue:
        check_issue_access(settings, issue_id)
        check_queue_access(settings, queue)
        return await ctx.request_context.lifespan_context.issues.issue_move_to_queue(
            issue_id,
            queue,
            move_all_fields=move_all_fields,
            initial_status=initial_status,
            expand=expand,
            notify=notify,
            extra=extra,
            auth=get_yandex_auth(ctx),
        )
