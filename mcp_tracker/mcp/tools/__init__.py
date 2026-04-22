"""MCP tools package for Yandex Tracker."""

from typing import Any

from mcp.server import FastMCP

from mcp_tracker.mcp.tools.automation import (
    register_automation_tools,
    register_automation_write_tools,
)
from mcp_tracker.mcp.tools.board import register_board_tools
from mcp_tracker.mcp.tools.board_write import register_board_write_tools
from mcp_tracker.mcp.tools.bulkchange import register_bulkchange_tools
from mcp_tracker.mcp.tools.component import (
    register_component_tools,
    register_component_write_tools,
)
from mcp_tracker.mcp.tools.dashboard import (
    register_dashboard_tools,
    register_dashboard_write_tools,
)
from mcp_tracker.mcp.tools.field import register_field_tools
from mcp_tracker.mcp.tools.filter import (
    register_filter_tools,
    register_filter_write_tools,
)
from mcp_tracker.mcp.tools.issue_extras import register_issue_extras_tools
from mcp_tracker.mcp.tools.issue_read import register_issue_read_tools
from mcp_tracker.mcp.tools.issue_write import register_issue_write_tools
from mcp_tracker.mcp.tools.project import (
    register_project_tools,
    register_project_write_tools,
)
from mcp_tracker.mcp.tools.queue import register_queue_tools
from mcp_tracker.mcp.tools.user import register_user_tools
from mcp_tracker.settings import Settings


def register_all_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register all MCP tools based on settings."""
    # Read-only tools — always registered
    register_queue_tools(settings, mcp)
    register_field_tools(settings, mcp)
    register_issue_read_tools(settings, mcp)
    register_user_tools(settings, mcp)
    register_board_tools(settings, mcp)
    register_filter_tools(settings, mcp)
    register_component_tools(settings, mcp)
    register_project_tools(settings, mcp)
    register_dashboard_tools(settings, mcp)
    register_automation_tools(settings, mcp)

    # Write tools — only in non read-only mode
    if not settings.tracker_read_only:
        register_issue_write_tools(settings, mcp)
        register_issue_extras_tools(settings, mcp)
        register_board_write_tools(settings, mcp)
        register_filter_write_tools(settings, mcp)
        register_component_write_tools(settings, mcp)
        register_project_write_tools(settings, mcp)
        register_dashboard_write_tools(settings, mcp)
        register_automation_write_tools(settings, mcp)
        register_bulkchange_tools(settings, mcp)


__all__ = ["register_all_tools"]
