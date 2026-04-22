"""Consolidated per-issue CRUD tools (comments, links, worklogs, attachments, checklist, tags).

Each tool takes an `action` argument so clients get a single tool per concept
instead of 3–5 separate ones. Write actions are gated by `settings.tracker_read_only`.
"""

import datetime
from typing import Annotated, Any, Literal, TypeVar

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from pydantic import BaseModel, Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import IssueID
from mcp_tracker.mcp.tools._access import check_issue_access, require_write_mode
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings


def _dump(value: Any) -> Any:
    """Serialize Pydantic models to dicts so FastMCP can ship them via `dict[str, Any]`."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True)
    if isinstance(value, list):
        return [_dump(v) for v in value]
    return value


CommentAction = Literal["get", "add", "update", "delete"]
LinkAction = Literal["get", "add", "delete"]
WorklogAction = Literal["get", "add", "update", "delete"]
AttachmentAction = Literal["get", "upload", "download", "delete"]
ChecklistAction = Literal["get", "add", "update", "delete", "clear"]
TagAction = Literal["add", "remove"]


_T = TypeVar("_T")


def _require(value: _T | None, name: str, action: str) -> _T:
    if value is None:
        raise ValueError(f"`{name}` is required for action `{action}`.")
    return value


def register_issue_parts_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register the 6 consolidated per-issue CRUD tools."""

    # ─── issue_comments ────────────────────────────────────────────────
    @mcp.tool(
        title="Issue Comments",
        description=(
            "Read or modify issue comments.\n\n"
            "Actions:\n"
            "- `get` → `{comments: [...]}` — list all comments\n"
            "- `add` → `{comment: {...}}` — requires `text`; use `summonees` to "
            "notify users (not `@login` in text)\n"
            "- `update` → `{comment: {...}}` — requires `comment_id` and `text`\n"
            "- `delete` → `{ok: true}` — requires `comment_id`"
        ),
    )
    async def issue_comments(
        ctx: Context[Any, AppContext],
        action: CommentAction,
        issue_id: IssueID,
        comment_id: Annotated[
            int | None, Field(description="Comment id (update/delete)")
        ] = None,
        text: Annotated[
            str | None, Field(description="Comment text (add/update)")
        ] = None,
        summonees: Annotated[
            list[str] | None,
            Field(description="Users to summon (logins/IDs). API-level mention."),
        ] = None,
        maillist_summonees: Annotated[
            list[str] | None, Field(description="Mailing lists to summon (emails)")
        ] = None,
        markup_type: Annotated[
            str | None, Field(description="Markup type, e.g. 'md' for YFM")
        ] = None,
        is_add_to_followers: Annotated[
            bool,
            Field(description="Add comment author to followers (add only)"),
        ] = True,
    ) -> dict[str, Any]:
        check_issue_access(settings, issue_id)
        issues = ctx.request_context.lifespan_context.issues
        auth = get_yandex_auth(ctx)

        if action == "get":
            items = await issues.issue_get_comments(issue_id, auth=auth)
            return {"comments": _dump(items)}

        require_write_mode(settings, action)

        if action == "add":
            text_ = _require(text, "text", action)
            comment = await issues.issue_add_comment(
                issue_id,
                text=text_,
                summonees=summonees,
                maillist_summonees=maillist_summonees,
                markup_type=markup_type,
                is_add_to_followers=is_add_to_followers,
                auth=auth,
            )
            return {"comment": _dump(comment)}
        if action == "update":
            cid = _require(comment_id, "comment_id", action)
            text_ = _require(text, "text", action)
            comment = await issues.issue_update_comment(
                issue_id,
                cid,
                text=text_,
                summonees=summonees,
                maillist_summonees=maillist_summonees,
                markup_type=markup_type,
                auth=auth,
            )
            return {"comment": _dump(comment)}
        if action == "delete":
            cid = _require(comment_id, "comment_id", action)
            await issues.issue_delete_comment(issue_id, cid, auth=auth)
            return {"ok": True}
        raise ValueError(f"Unknown action: {action}")

    # ─── issue_links ────────────────────────────────────────────────
    @mcp.tool(
        title="Issue Links",
        description=(
            "Read or modify issue links.\n\n"
            "Actions:\n"
            "- `get` → `{links: [...]}` — list related issues\n"
            "- `add` → `{link: {...}}` — requires `relationship` and `target_issue` "
            "(e.g. relates, depends on, is dependent by, duplicates, is epic of, ...)\n"
            "- `delete` → `{ok: true}` — requires `link_id`"
        ),
    )
    async def issue_links(
        ctx: Context[Any, AppContext],
        action: LinkAction,
        issue_id: IssueID,
        relationship: Annotated[
            str | None, Field(description="Link relationship (add)")
        ] = None,
        target_issue: Annotated[
            str | None, Field(description="Target issue key, e.g. 'PROJ-2' (add)")
        ] = None,
        link_id: Annotated[int | None, Field(description="Link id (delete)")] = None,
    ) -> dict[str, Any]:
        check_issue_access(settings, issue_id)
        issues = ctx.request_context.lifespan_context.issues
        auth = get_yandex_auth(ctx)

        if action == "get":
            items = await issues.issues_get_links(issue_id, auth=auth)
            return {"links": _dump(items)}

        require_write_mode(settings, action)

        if action == "add":
            rel = _require(relationship, "relationship", action)
            tgt = _require(target_issue, "target_issue", action)
            link = await issues.issue_add_link(
                issue_id,
                relationship=rel,
                target_issue=tgt,
                auth=auth,
            )
            return {"link": _dump(link)}
        if action == "delete":
            lid = _require(link_id, "link_id", action)
            await issues.issue_delete_link(issue_id, lid, auth=auth)
            return {"ok": True}
        raise ValueError(f"Unknown action: {action}")

    # ─── issue_worklogs ────────────────────────────────────────────────
    @mcp.tool(
        title="Issue Worklogs",
        description=(
            "Read or modify time-tracking worklogs on an issue.\n\n"
            "Actions:\n"
            "- `get` → `{worklogs: [...]}`\n"
            "- `add` → `{worklog: {...}}` — requires `duration` (ISO-8601, e.g. 'PT1H30M'); "
            "`start` defaults to current UTC server-side if omitted\n"
            "- `update` → `{worklog: {...}}` — requires `worklog_id`; at least one of "
            "`duration`, `comment`, `start`\n"
            "- `delete` → `{ok: true}` — requires `worklog_id`"
        ),
    )
    async def issue_worklogs(
        ctx: Context[Any, AppContext],
        action: WorklogAction,
        issue_id: IssueID,
        worklog_id: Annotated[
            int | None, Field(description="Worklog id (update/delete)")
        ] = None,
        duration: Annotated[
            str | None, Field(description="ISO-8601 duration (add/update)")
        ] = None,
        comment: Annotated[
            str | None, Field(description="Worklog comment (add/update)")
        ] = None,
        start: Annotated[
            datetime.datetime | None,
            Field(description="Start datetime; UTC if tz absent (add/update)"),
        ] = None,
    ) -> dict[str, Any]:
        check_issue_access(settings, issue_id)
        issues = ctx.request_context.lifespan_context.issues
        auth = get_yandex_auth(ctx)

        if action == "get":
            items = await issues.issue_get_worklogs(issue_id, auth=auth)
            return {"worklogs": _dump(items or [])}

        require_write_mode(settings, action)

        if action == "add":
            dur = _require(duration, "duration", action)
            worklog = await issues.issue_add_worklog(
                issue_id,
                duration=dur,
                comment=comment,
                start=start,
                auth=auth,
            )
            return {"worklog": _dump(worklog)}
        if action == "update":
            wid = _require(worklog_id, "worklog_id", action)
            worklog = await issues.issue_update_worklog(
                issue_id,
                wid,
                duration=duration,
                comment=comment,
                start=start,
                auth=auth,
            )
            return {"worklog": _dump(worklog)}
        if action == "delete":
            wid = _require(worklog_id, "worklog_id", action)
            await issues.issue_delete_worklog(issue_id, wid, auth=auth)
            return {"ok": True}
        raise ValueError(f"Unknown action: {action}")

    # ─── issue_attachments ────────────────────────────────────────────────
    @mcp.tool(
        title="Issue Attachments",
        description=(
            "Read, upload, download or delete attachments.\n\n"
            "Actions:\n"
            "- `get` → `{attachments: [...]}`\n"
            "- `upload` → `{attachment: {...}}` — provide EXACTLY ONE source: "
            "`file_path` (server FS), `content_base64` + `filename`, or "
            "`source_url` (HTTPS, host must be in "
            "TRACKER_ATTACHMENT_URL_ALLOWED_DOMAINS; redirects not followed)\n"
            "- `download` → `{path?: str, content_base64?: str}` — requires `attachment_id` "
            "and `filename`; use `dest_path` and/or `return_base64=True`\n"
            "- `delete` → `{ok: true}` — requires `attachment_id`"
        ),
    )
    async def issue_attachments(
        ctx: Context[Any, AppContext],
        action: AttachmentAction,
        issue_id: IssueID,
        attachment_id: Annotated[
            str | None, Field(description="Attachment id (download/delete)")
        ] = None,
        filename: Annotated[
            str | None,
            Field(
                description="Upload: label in Tracker (required with content_base64; "
                "derived from URL path for source_url). "
                "Download: server-side attachment filename."
            ),
        ] = None,
        file_path: Annotated[
            str | None,
            Field(description="Path on the MCP server host (upload)."),
        ] = None,
        content_base64: Annotated[
            str | None,
            Field(description="Base64 file bytes (upload)."),
        ] = None,
        source_url: Annotated[
            str | None,
            Field(
                description="HTTPS URL to fetch (upload). Host must be in the "
                "operator-configured allowlist; off by default."
            ),
        ] = None,
        dest_path: Annotated[
            str | None,
            Field(description="Destination file/dir on server (download)."),
        ] = None,
        return_base64: Annotated[
            bool,
            Field(description="Return bytes as base64 in response (download)."),
        ] = False,
    ) -> dict[str, Any]:
        check_issue_access(settings, issue_id)
        issues = ctx.request_context.lifespan_context.issues
        auth = get_yandex_auth(ctx)

        if action == "get":
            items = await issues.issue_get_attachments(issue_id, auth=auth)
            return {"attachments": _dump(items)}
        if action == "download":
            aid = _require(attachment_id, "attachment_id", action)
            fname = _require(filename, "filename", action)
            return await issues.issue_download_attachment(
                issue_id,
                aid,
                fname,
                dest_path=dest_path,
                return_base64=return_base64,
                auth=auth,
            )

        require_write_mode(settings, action)

        if action == "upload":
            # Exactly one source must be given.
            sources = [s for s in (file_path, content_base64, source_url) if s]
            if len(sources) != 1:
                raise ValueError(
                    "Provide exactly one of `file_path`, `content_base64`, or "
                    "`source_url` for upload."
                )

            effective_b64 = content_base64
            effective_filename = filename

            if source_url is not None:
                from mcp_tracker.mcp.url_fetch import (
                    UrlFetchError,
                    fetch_attachment,
                )

                try:
                    data, suggested = await fetch_attachment(
                        source_url,
                        allowed_domains=settings.tracker_attachment_url_allowed_domains,
                        max_bytes=settings.tracker_attachment_url_max_bytes,
                        timeout_seconds=settings.tracker_attachment_url_timeout_seconds,
                    )
                except UrlFetchError as e:
                    raise ValueError(f"Cannot fetch source_url: {e}") from e

                import base64 as _base64

                effective_b64 = _base64.b64encode(data).decode("ascii")
                effective_filename = filename or suggested or "attachment"

            attachment = await issues.issue_upload_attachment(
                issue_id,
                file_path=file_path,
                content_base64=effective_b64,
                filename=effective_filename,
                auth=auth,
            )
            return {"attachment": _dump(attachment)}
        if action == "delete":
            aid = _require(attachment_id, "attachment_id", action)
            await issues.issue_delete_attachment(issue_id, aid, auth=auth)
            return {"ok": True}
        raise ValueError(f"Unknown action: {action}")

    # ─── issue_checklist ────────────────────────────────────────────────
    @mcp.tool(
        title="Issue Checklist",
        description=(
            "Manage issue checklist items.\n\n"
            "Actions:\n"
            "- `get` → `{checklist: [...]}`\n"
            "- `add` → `{checklist: [...]}` — requires `text`; accepts `checked`, "
            "`assignee`, `deadline`\n"
            "- `update` → `{checklist: [...]}` — requires `item_id`; any of "
            "`text/checked/assignee/deadline`\n"
            "- `delete` → `{ok: true, remaining: [...]}` — requires `item_id`\n"
            "- `clear` → `{ok: true}` — remove all items"
        ),
    )
    async def issue_checklist(
        ctx: Context[Any, AppContext],
        action: ChecklistAction,
        issue_id: IssueID,
        item_id: Annotated[
            str | None, Field(description="Checklist item id (update/delete)")
        ] = None,
        text: Annotated[str | None, Field(description="Item text (add/update)")] = None,
        checked: Annotated[
            bool | None, Field(description="Checked state (add/update)")
        ] = None,
        assignee: Annotated[
            str | int | None,
            Field(description="Assignee login or uid (add/update)"),
        ] = None,
        deadline: Annotated[
            dict[str, Any] | None,
            Field(description="Deadline object {date, deadlineType, isExceeded?}"),
        ] = None,
    ) -> dict[str, Any]:
        check_issue_access(settings, issue_id)
        issues = ctx.request_context.lifespan_context.issues
        auth = get_yandex_auth(ctx)

        if action == "get":
            items = await issues.issue_get_checklist(issue_id, auth=auth)
            return {"checklist": _dump(items)}

        require_write_mode(settings, action)

        if action == "add":
            text_ = _require(text, "text", action)
            items = await issues.issue_add_checklist_item(
                issue_id,
                text=text_,
                checked=checked,
                assignee=assignee,
                deadline=deadline,
                auth=auth,
            )
            return {"checklist": _dump(items)}
        if action == "update":
            iid = _require(item_id, "item_id", action)
            items = await issues.issue_update_checklist_item(
                issue_id,
                iid,
                text=text,
                checked=checked,
                assignee=assignee,
                deadline=deadline,
                auth=auth,
            )
            return {"checklist": _dump(items)}
        if action == "delete":
            iid = _require(item_id, "item_id", action)
            remaining = await issues.issue_delete_checklist_item(
                issue_id, iid, auth=auth
            )
            return {
                "ok": True,
                "remaining": _dump(remaining) if remaining else [],
            }
        if action == "clear":
            await issues.issue_clear_checklist(issue_id, auth=auth)
            return {"ok": True}
        raise ValueError(f"Unknown action: {action}")

    # ─── issue_tags ────────────────────────────────────────────────
    @mcp.tool(
        title="Issue Tags",
        description=(
            "Add or remove tags on an issue.\n\n"
            "Actions:\n"
            "- `add` → updated issue; appends to existing tags\n"
            "- `remove` → updated issue; removes the given tags"
        ),
    )
    async def issue_tags(
        ctx: Context[Any, AppContext],
        action: TagAction,
        issue_id: IssueID,
        tags: Annotated[list[str], Field(description="Tags to add or remove")],
    ) -> dict[str, Any]:
        check_issue_access(settings, issue_id)
        require_write_mode(settings, action)

        issues = ctx.request_context.lifespan_context.issues
        auth = get_yandex_auth(ctx)

        if action == "add":
            issue = await issues.issue_add_tags(issue_id, tags, auth=auth)
            return {"issue": _dump(issue)}
        if action == "remove":
            issue = await issues.issue_remove_tags(issue_id, tags, auth=auth)
            return {"issue": _dump(issue)}
        raise ValueError(f"Unknown action: {action}")
