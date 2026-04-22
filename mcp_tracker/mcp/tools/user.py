"""Consolidated users tool (list/search/get/current)."""

from typing import Annotated, Any, Literal

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from pydantic import BaseModel, Field
from thefuzz import process

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.mcp.params import PageParam, PerPageParam
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.users import User

UserAction = Literal["list", "search", "get", "current"]


def _dump(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True)
    if isinstance(value, list):
        return [_dump(v) for v in value]
    return value


def register_user_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register consolidated users tool (all read-only)."""

    @mcp.tool(
        title="Users",
        description=(
            "Look up users in the organization.\n\n"
            "Actions:\n"
            "- `list` → `{users: [...]}` — paginated org users\n"
            "- `search` → `{users: [...]}` — requires `query` (login/email/name); "
            "exact match on login or email returns [user]; otherwise fuzzy-match on full name\n"
            "- `get` → user; requires `user_id` (login or uid)\n"
            "- `current` → authenticated user"
        ),
    )
    async def users(
        ctx: Context[Any, AppContext],
        action: UserAction,
        user_id: Annotated[
            str | None, Field(description="User login or uid (get)")
        ] = None,
        query: Annotated[
            str | None, Field(description="login/email/name to search (search)")
        ] = None,
        page: PageParam = 1,
        per_page: PerPageParam = 25,
    ) -> dict[str, Any]:
        users_proto = ctx.request_context.lifespan_context.users
        auth = get_yandex_auth(ctx)

        if action == "list":
            items = await users_proto.users_list(
                per_page=per_page, page=page, auth=auth
            )
            return {"users": _dump(items)}

        if action == "search":
            if query is None:
                raise ValueError("`query` is required for action `search`.")
            needle = query.strip().lower()

            search_per_page = 100
            current = 1
            all_users: list[User] = []
            while True:
                batch = await users_proto.users_list(
                    per_page=search_per_page, page=current, auth=auth
                )
                if not batch:
                    break
                for user in batch:
                    if user.login and needle == user.login.strip().lower():
                        return {"users": _dump([user])}
                    if user.email and needle == user.email.strip().lower():
                        return {"users": _dump([user])}
                all_users.extend(batch)
                current += 1

            names = {
                idx: f"{u.first_name} {u.last_name}" for idx, u in enumerate(all_users)
            }
            results = process.extractBests(needle, names, score_cutoff=80, limit=3)
            matched = [all_users[idx] for _name, _score, idx in results]
            return {"users": _dump(matched)}

        if action == "get":
            if user_id is None:
                raise ValueError("`user_id` is required for action `get`.")
            fetched = await users_proto.user_get(user_id, auth=auth)
            if fetched is None:
                raise TrackerError(f"User `{user_id}` not found.")
            return {"user": _dump(fetched)}

        if action == "current":
            me = await users_proto.user_get_current(auth=auth)
            return {"user": _dump(me)}

        raise ValueError(f"Unknown action: {action}")
