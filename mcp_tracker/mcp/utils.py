from collections.abc import Iterable
from typing import Any, TypeVar

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.fastmcp import Context
from pydantic import BaseModel
from starlette.requests import Request

from mcp_tracker.tracker.proto.common import YandexAuth

T = TypeVar("T", bound=BaseModel)


def get_yandex_auth(ctx: Context[Any, Any, Request]) -> YandexAuth:
    access_token = get_access_token()
    token = access_token.token if access_token else None

    auth = YandexAuth(token=token)

    if ctx.request_context.request is not None:
        cloud_org_id = ctx.request_context.request.query_params.get("cloudOrgId")
        org_id = ctx.request_context.request.query_params.get("orgId")

        if cloud_org_id:
            cloud_org_id = cloud_org_id.strip()
            auth.cloud_org_id = cloud_org_id or None

        if org_id:
            org_id = org_id.strip()
            auth.org_id = org_id or None

    return auth


def set_non_needed_fields_null(data: Iterable[T], needed_fields: set[str]) -> None:
    for item in data:
        for field in item.model_fields_set:
            if field not in needed_fields:
                setattr(item, field, None)


def strip_extra_fields(item: BaseModel, keys: Iterable[str]) -> None:
    """Remove `model_extra` keys (declared via extra='allow') from a Pydantic model.

    Used to drop noisy/org-specific fields like `favorite` / `qaEngineer` that
    Tracker returns on every issue and that bloat LLM context for no gain.
    """
    extra = item.__pydantic_extra__
    if not extra:
        return
    for key in keys:
        extra.pop(key, None)
