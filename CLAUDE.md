# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Yandex Tracker is a Model Context Protocol (MCP) server that provides tools for interacting with Yandex Tracker API. It implements a FastMCP server with protocol-based architecture and optional Redis caching.

## Commands

```bash
task              # Run all checks (format, lint, type checking, tests) - REQUIRED before commits
task format       # Auto-format code
task check        # Run type and format checking
task test         # Run tests
uv sync           # Install dependencies
uv run mcp-tracker # Run the server
```

## Architecture

- **Protocols** (`mcp_tracker/tracker/proto/`): Define API contracts (`IssueProtocol`, `QueuesProtocol`, etc.)
- **Client** (`mcp_tracker/tracker/custom/client.py`): Implements protocols, handles HTTP requests
- **Caching** (`mcp_tracker/tracker/caching/client.py`): Wraps protocols with Redis caching
- **MCP Server** (`mcp_tracker/mcp/server.py`): Server creation and configuration
- **MCP Tools** (`mcp_tracker/mcp/tools/`): Consolidated tool surface (~27 tools total).
  Each tool is action-based (`action=...`). Write actions are gated internally
  via `require_write_mode()` when `tracker_read_only=True`.
  - `_access.py`: Access control + read-only gate (`check_issue_access`, `check_queue_access`, `require_write_mode`)
  - `field.py`: `tracker_reference(kind=...)` + `issue_get_url`
  - `queue.py`: `queues(action=...)` — list/tags/versions/fields/metadata/create
  - `user.py`: `users(action=...)` — list/search/get/current
  - `issue_read.py`: `issue_get`, `issues_find`, `issues_count`, `issue_get_transitions`
  - `issue_write.py`: `issue_create/update/close/execute_transition`
  - `issue_extras.py`: `issue_move_to_queue`
  - `issue_parts.py`: `issue_comments/links/worklogs/attachments/checklist/tags` (action-based)
  - `crud.py`: `components/filters/dashboards/sprints` (action-based)
  - `board.py`: `boards(action=...)` + `board_columns(action=...)`
  - `automation.py`: `triggers/autoactions/macros/workflows` (action-based)
  - `bulkchange.py`: `bulk(action=update/move/transition/status)`
  - `project.py`: entity tools for projects/portfolios/goals
  - `__init__.py`: `register_all_tools()` orchestrator
- **Settings** (`mcp_tracker/settings.py`): Pydantic settings from environment variables
- All protocol methods accept optional `auth: YandexAuth | None` parameter for OAuth support.
- All Pydantic models for Yandex Tracker entities inherit from `BaseTrackerEntity`.

## Testing

### Rules

- Use **pytest** with asyncio mode `auto`
- Use **aioresponses** for HTTP mocking in `TrackerClient` tests and `@tests/aioresponses_utils.py` for capturing request/response pairs.
- Use **AsyncMock** with `spec=` for protocol mocking in MCP tool tests
- Always type-hint all parameters including fixtures
- Never import inside functions - all imports at top of file
- Never use loops for test cases - use `@pytest.mark.parametrize`
- Use `model_construct()` for creating Pydantic model fixtures (skips validation)

### Test Locations

| What to test               | Where                                      |
|----------------------------|--------------------------------------------|
| TrackerClient HTTP methods | `tests/tracker/custom/test_*.py`           |
| Caching wrappers           | `tests/tracker/caching/test_*_protocol.py` |
| MCP tools                  | `tests/mcp/tools/test_*_tools.py`          |
| OAuth provider             | `tests/mcp/oauth/`                         |

### Testing TrackerClient (HTTP layer)

Use `aioresponses` to mock HTTP requests. Verify request headers and response parsing:

```python
async def test_api_method(self, client: TrackerClient) -> None:
    with aioresponses() as m:
        m.get("https://api.tracker.yandex.net/v3/endpoint", payload={"key": "value"})
        result = await client.api_method()
        assert result.key == "value"
```

### Testing MCP Tools

MCP tools are tested via `ClientSession.call_tool()` against a real `FastMCP` server with mocked protocols.

Key fixtures (from `tests/mcp/conftest.py`):
- `client_session`: Connected MCP client session
- `client_session_with_limits`: Session with queue restrictions enabled
- `mock_issues_protocol`, `mock_queues_protocol`, etc.: Mocked protocol instances

Use `get_tool_result_content(result)` helper to extract tool return values.

```python
async def test_tool(self, client_session: ClientSession, mock_issues_protocol: AsyncMock) -> None:
    mock_issues_protocol.issue_get.return_value = sample_issue
    result = await client_session.call_tool("issue_get", {"issue_id": "TEST-1"})
    assert not result.isError
    content = get_tool_result_content(result)
    assert content["key"] == "TEST-1"
```

For paginated methods, use `side_effect` for sequential returns: `mock.method.side_effect = [page1, []]`

## Adding New MCP Tools

### Implementation Checklist

1. **Protocol**: Add method signature to `mcp_tracker/tracker/proto/*.py`
2. **Client**: Implement in `mcp_tracker/tracker/custom/client.py`
3. **Caching**: Add wrapper in `mcp_tracker/tracker/caching/client.py`
4. **Tool**: Prefer adding a new action to an existing consolidated tool (e.g. a new
   `component` op goes as a new `action` branch in `crud.py → components`). Only add
   a separate tool when it's a genuinely new concept that doesn't fit any family.
   - Consolidated families live in: `field.py` (tracker_reference), `queue.py` (queues),
     `user.py` (users), `issue_parts.py` (issue_comments/links/worklogs/attachments/
     checklist/tags), `crud.py` (components/filters/dashboards/sprints), `board.py`
     (boards/board_columns), `automation.py` (triggers/autoactions/macros/workflows),
     `bulkchange.py` (bulk).
   - Standalone issue ops live in `issue_read.py` / `issue_write.py` / `issue_extras.py`.
5. **Tests**: Add to the matching `tests/mcp/tools/test_*_tools.py` (or `test_issue_parts_tools.py` / `test_crud_tools.py` / `test_automation_tools.py` / `test_bulk_tools.py`)
6. **Docs**: Update `README.md`, `README_ru.md`, and `manifest.json` if the tool surface changes

### Read-only gating

Consolidated tools are registered in every mode. When a caller invokes a write
`action`, the tool calls `require_write_mode(settings, action)` first, which
raises `TrackerError` if `settings.tracker_read_only=True`. Pure write-only
tools (e.g. `issue_create`, `entity_create`) still live in their own
`*_write_tools` registration and are gated at registration time.

### Test Requirements for New Tools

- Test each `action` with its required parameters
- Verify that missing required parameters yield an error
- For write actions on consolidated tools, add a `client_session_read_only` test asserting the action is blocked
- Test queue restrictions with `client_session_with_limits` if the tool touches issues/queues
- Add the tool name to the matching list in `tests/mcp/server/test_server_creation.py`
  (`READ_ONLY_TOOL_NAMES` for anything always registered, `WRITE_TOOL_NAMES` for write-only tools)

## Configuration

Authentication (one required):
- `TRACKER_TOKEN`: Static OAuth token
- `TRACKER_IAM_TOKEN`: Static IAM token
- `TRACKER_SA_*`: Service account credentials for dynamic IAM tokens

Organization (one required):
- `TRACKER_CLOUD_ORG_ID`: For Yandex Cloud
- `TRACKER_ORG_ID`: For on-premise

Optional:
- `TRACKER_LIMIT_QUEUES`: Restrict access to specific queues
- `TRACKER_READ_ONLY`: When `true`, disables write tools (issue_create, issue_update, issue_close, issue_execute_transition)
- `TOOLS_CACHE_ENABLED`: Enable Redis caching
- `OAUTH_ENABLED`: Enable OAuth provider mode
