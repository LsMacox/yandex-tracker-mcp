"""Convert structured filter dicts into Yandex Tracker YQL fragments.

The tool-layer feeds `filter={queue: "TEST", resolution: "empty"}`-style dicts
into this helper before hitting the API. The Tracker `filter` body parameter
accepts many layouts but rejects a surprising number of common combinations
with HTTP 422 — building YQL client-side gives us one predictable codepath.
"""

from typing import Any

# Known aliases: structured-filter key → YQL field name.
# Tracker YQL is case-sensitive and field names are PascalCase; we normalize
# lowercase `queue` → `Queue`, handle the Boards/Board plural trap, etc.
_FIELD_ALIASES: dict[str, str] = {
    "queue": "Queue",
    "key": "Key",
    "keys": "Key",
    "status": "Status",
    "type": "Type",
    "priority": "Priority",
    "resolution": "Resolution",
    "assignee": "Assignee",
    "author": "Author",
    "follower": "Follower",
    "followers": "Follower",
    "summary": "Summary",
    "description": "Description",
    "tags": "Tags",
    "tag": "Tags",
    "components": "Components",
    "component": "Components",
    "version": "Version",
    "versions": "Version",
    "affected_versions": "AffectedVersions",
    "fix_versions": "FixVersions",
    "sprint": "Sprint",
    "epic": "Epic",
    "parent": "Parent",
    "board": "Boards",
    "boards": "Boards",
    "project": "Project",
    "created": "Created",
    "updated": "Updated",
    "resolved": "Resolved",
    "due_date": "Due",
    "deadline": "Due",
    "start_date": "StartDate",
    "end_date": "EndDate",
    "story_points": "StoryPoints",
    "estimation": "Estimation",
    "spent": "Spent",
    "original_estimation": "OriginalEstimation",
}

# Zero-arg YQL functions (plain strings in input → `name()` in output).
_MAGIC_VALUES: dict[str, str] = {
    "empty": "empty()",
    "notempty": "notEmpty()",
    "not_empty": "notEmpty()",
    "me": "me()",
    "today": "today()",
    "yesterday": "yesterday()",
    "tomorrow": "tomorrow()",
    "now": "now()",
    "week": "week()",
    "month": "month()",
    "quarter": "quarter()",
    "year": "year()",
    "unresolved": "empty()",
    "resolved": "notEmpty()",
}

# YAML-safe: identifiers that don't need quoting in YQL (letters, digits,
# underscores, and the dot used in some local field ids like `myField.foo`).
_BARE_IDENT_CHARS = set(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
)


class FilterConversionError(ValueError):
    """Raised when a structured filter can't be rendered as YQL."""


def _needs_quoting(value: str) -> bool:
    if not value:
        return True
    # YQL function calls are written bare.
    if value.endswith("()"):
        return False
    return any(ch not in _BARE_IDENT_CHARS for ch in value)


def _quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _format_scalar(value: Any) -> str:
    """Render a scalar value as a YQL token."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return "empty()"

    text = str(value).strip()
    magic = _MAGIC_VALUES.get(text.lower())
    if magic is not None:
        return magic

    if _needs_quoting(text):
        return _quote(text)
    return text


def _normalize_field(key: str) -> str:
    """Map a structured-filter key onto its YQL field name."""
    alias = _FIELD_ALIASES.get(key.lower())
    if alias is not None:
        return alias
    # Leave custom/local-field keys alone — they already use whatever the
    # Tracker admin configured (often camelCase like `storyPoints`).
    return key


def _format_range(field: str, value: dict[str, Any]) -> str:
    """Render `{from, to}` / `{gt, lt, ...}` dict as a YQL clause."""
    from_ = value.get("from", value.get("gte"))
    to = value.get("to", value.get("lte"))
    gt = value.get("gt")
    lt = value.get("lt")

    # `{from, to}` → `Created: 2024-01-01 .. 2024-12-31`
    if from_ is not None and to is not None and gt is None and lt is None:
        return f"{field}: {_format_scalar(from_)} .. {_format_scalar(to)}"

    parts: list[str] = []
    if from_ is not None:
        parts.append(f"{field}: >= {_format_scalar(from_)}")
    if gt is not None:
        parts.append(f"{field}: > {_format_scalar(gt)}")
    if to is not None:
        parts.append(f"{field}: <= {_format_scalar(to)}")
    if lt is not None:
        parts.append(f"{field}: < {_format_scalar(lt)}")

    if not parts:
        raise FilterConversionError(
            f"Range filter for `{field}` has no recognized keys "
            f"(expected from/to/gt/lt/gte/lte), got: {sorted(value)}"
        )
    if len(parts) == 1:
        return parts[0]
    return "(" + " AND ".join(parts) + ")"


def _render_clause(key: str, value: Any) -> str:
    field = _normalize_field(key)

    # List → OR-list, rendered as `Field: a, b, c` (YQL supports this shape
    # for all enum-ish fields).
    if isinstance(value, list):
        if not value:
            raise FilterConversionError(
                f"Empty list for `{key}` — Tracker rejects `Field:` without values."
            )
        rendered = ", ".join(_format_scalar(v) for v in value)
        return f"{field}: {rendered}"

    if isinstance(value, dict):
        return _format_range(field, value)

    return f"{field}: {_format_scalar(value)}"


def filter_to_yql(filter_dict: dict[str, Any]) -> str:
    """Render a structured filter dict as a YQL query fragment.

    Examples:
        >>> filter_to_yql({"queue": "TEST"})
        'Queue: TEST'
        >>> filter_to_yql({"queue": "TEST", "resolution": "empty", "assignee": "me"})
        'Queue: TEST AND Resolution: empty() AND Assignee: me()'
        >>> filter_to_yql({"status": ["open", "inProgress"]})
        'Status: open, inProgress'
        >>> filter_to_yql({"board": "My Board"})
        'Boards: "My Board"'
        >>> filter_to_yql({"created": {"from": "2024-01-01", "to": "2024-12-31"}})
        'Created: 2024-01-01 .. 2024-12-31'
    """
    if not filter_dict:
        raise FilterConversionError("Empty filter dict — nothing to convert.")

    clauses = [_render_clause(k, v) for k, v in filter_dict.items()]
    return " AND ".join(clauses)


def order_to_sort_by(order: list[str]) -> str:
    """Convert `['-updated', '+priority']` → `"Sort By": Updated DESC, Priority ASC`.

    Empty input returns an empty string (caller concatenates conditionally).
    """
    if not order:
        return ""
    parts: list[str] = []
    for item in order:
        direction = "ASC"
        raw = item
        if raw.startswith("-"):
            direction = "DESC"
            raw = raw[1:]
        elif raw.startswith("+"):
            raw = raw[1:]
        field = _normalize_field(raw)
        parts.append(f"{field} {direction}")
    return '"Sort By": ' + ", ".join(parts)
