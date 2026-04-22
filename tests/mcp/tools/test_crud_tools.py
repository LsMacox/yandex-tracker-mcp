"""Tests for consolidated CRUD tools: components/filters/dashboards/sprints."""

from unittest.mock import AsyncMock

import pytest
from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.boards import BoardReference, Sprint
from mcp_tracker.tracker.proto.types.misc import (
    Component,
    Dashboard,
    DashboardWidget,
    IssueFilter,
)
from tests.mcp.conftest import get_tool_result_content

# ─── fixtures ────────────────────────────────────────────────


@pytest.fixture
def sample_component() -> Component:
    return Component.model_construct(id=1, name="Core", version=1)


@pytest.fixture
def sample_components(sample_component: Component) -> list[Component]:
    return [
        sample_component,
        Component.model_construct(id=2, name="Infra", version=1),
    ]


@pytest.fixture
def sample_filter() -> IssueFilter:
    return IssueFilter.model_construct(id="101", name="My filter", query="Queue: TEST")


@pytest.fixture
def sample_filters(sample_filter: IssueFilter) -> list[IssueFilter]:
    return [sample_filter]


@pytest.fixture
def sample_dashboard() -> Dashboard:
    return Dashboard.model_construct(id="d1", name="Main")


@pytest.fixture
def sample_dashboards(sample_dashboard: Dashboard) -> list[Dashboard]:
    return [sample_dashboard]


@pytest.fixture
def sample_widgets() -> list[DashboardWidget]:
    return [DashboardWidget.model_construct(id="w1", type="issueList")]


@pytest.fixture
def sample_sprint() -> Sprint:
    return Sprint.model_construct(
        id=44,
        name="Sprint 1",
        status="draft",
        board=BoardReference.model_construct(id=73, display="My Board"),
    )


# ─── components ────────────────────────────────────────────────


class TestComponents:
    async def test_list(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_components: list[Component],
    ) -> None:
        mock_components_protocol.components_list.return_value = sample_components

        result = await client_session.call_tool("components", {"action": "list"})

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["components"]) == len(sample_components)

    async def test_get(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_component: Component,
    ) -> None:
        mock_components_protocol.component_get.return_value = sample_component

        result = await client_session.call_tool(
            "components", {"action": "get", "component_id": 1}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["component"]["id"] == sample_component.id

    async def test_create(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_component: Component,
    ) -> None:
        mock_components_protocol.component_create.return_value = sample_component

        result = await client_session.call_tool(
            "components",
            {"action": "create", "name": "Core", "queue": "TEST"},
        )

        assert not result.isError
        call_kwargs = mock_components_protocol.component_create.call_args.kwargs
        assert call_kwargs["name"] == "Core"
        assert call_kwargs["queue"] == "TEST"

    async def test_update_autofetches_version(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_component: Component,
    ) -> None:
        mock_components_protocol.component_get.return_value = sample_component
        mock_components_protocol.component_update.return_value = sample_component

        result = await client_session.call_tool(
            "components",
            {
                "action": "update",
                "component_id": 1,
                "fields": {"name": "Updated"},
            },
        )

        assert not result.isError
        # version fetched from component_get
        mock_components_protocol.component_get.assert_called_once()
        call_kwargs = mock_components_protocol.component_update.call_args.kwargs
        assert call_kwargs["version"] == sample_component.version

    async def test_delete(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
    ) -> None:
        mock_components_protocol.component_delete.return_value = None

        result = await client_session.call_tool(
            "components", {"action": "delete", "component_id": 1}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content == {"ok": True}

    async def test_read_only_blocks_create(
        self,
        client_session_read_only: ClientSession,
        mock_components_protocol: AsyncMock,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "components",
            {"action": "create", "name": "x", "queue": "TEST"},
        )
        assert result.isError
        mock_components_protocol.component_create.assert_not_called()


# ─── filters ────────────────────────────────────────────────


class TestFilters:
    async def test_list(
        self,
        client_session: ClientSession,
        mock_filters_protocol: AsyncMock,
        sample_filters: list[IssueFilter],
    ) -> None:
        mock_filters_protocol.filters_list.return_value = sample_filters

        result = await client_session.call_tool("filters", {"action": "list"})

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["filters"]) == len(sample_filters)

    async def test_get(
        self,
        client_session: ClientSession,
        mock_filters_protocol: AsyncMock,
        sample_filter: IssueFilter,
    ) -> None:
        mock_filters_protocol.filter_get.return_value = sample_filter

        result = await client_session.call_tool(
            "filters", {"action": "get", "filter_id": "101"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["filter"]["id"] == sample_filter.id

    async def test_create(
        self,
        client_session: ClientSession,
        mock_filters_protocol: AsyncMock,
        sample_filter: IssueFilter,
    ) -> None:
        mock_filters_protocol.filter_create.return_value = sample_filter

        result = await client_session.call_tool(
            "filters",
            {"action": "create", "name": "My", "query": "Queue: TEST"},
        )

        assert not result.isError
        call_kwargs = mock_filters_protocol.filter_create.call_args.kwargs
        assert call_kwargs["query"] == "Queue: TEST"

    async def test_update(
        self,
        client_session: ClientSession,
        mock_filters_protocol: AsyncMock,
        sample_filter: IssueFilter,
    ) -> None:
        mock_filters_protocol.filter_update.return_value = sample_filter

        result = await client_session.call_tool(
            "filters",
            {"action": "update", "filter_id": "101", "fields": {"name": "New"}},
        )

        assert not result.isError

    async def test_delete(
        self,
        client_session: ClientSession,
        mock_filters_protocol: AsyncMock,
    ) -> None:
        mock_filters_protocol.filter_delete.return_value = None

        result = await client_session.call_tool(
            "filters", {"action": "delete", "filter_id": "101"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content == {"ok": True}


# ─── dashboards ────────────────────────────────────────────────


class TestDashboards:
    async def test_list(
        self,
        client_session: ClientSession,
        mock_dashboards_protocol: AsyncMock,
        sample_dashboards: list[Dashboard],
    ) -> None:
        mock_dashboards_protocol.dashboards_list.return_value = sample_dashboards

        result = await client_session.call_tool("dashboards", {"action": "list"})

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["dashboards"]) == len(sample_dashboards)

    async def test_get(
        self,
        client_session: ClientSession,
        mock_dashboards_protocol: AsyncMock,
        sample_dashboard: Dashboard,
    ) -> None:
        mock_dashboards_protocol.dashboard_get.return_value = sample_dashboard

        result = await client_session.call_tool(
            "dashboards", {"action": "get", "dashboard_id": "d1"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["dashboard"]["id"] == sample_dashboard.id

    async def test_widgets(
        self,
        client_session: ClientSession,
        mock_dashboards_protocol: AsyncMock,
        sample_widgets: list[DashboardWidget],
    ) -> None:
        mock_dashboards_protocol.dashboard_get_widgets.return_value = sample_widgets

        result = await client_session.call_tool(
            "dashboards", {"action": "widgets", "dashboard_id": "d1"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["widgets"]) == len(sample_widgets)

    async def test_create(
        self,
        client_session: ClientSession,
        mock_dashboards_protocol: AsyncMock,
        sample_dashboard: Dashboard,
    ) -> None:
        mock_dashboards_protocol.dashboard_create.return_value = sample_dashboard

        result = await client_session.call_tool(
            "dashboards", {"action": "create", "name": "Ops"}
        )

        assert not result.isError

    async def test_update_with_version(
        self,
        client_session: ClientSession,
        mock_dashboards_protocol: AsyncMock,
        sample_dashboard: Dashboard,
    ) -> None:
        mock_dashboards_protocol.dashboard_update.return_value = sample_dashboard

        result = await client_session.call_tool(
            "dashboards",
            {
                "action": "update",
                "dashboard_id": "d1",
                "fields": {"name": "New"},
                "version": 5,
            },
        )

        assert not result.isError
        call_kwargs = mock_dashboards_protocol.dashboard_update.call_args.kwargs
        assert call_kwargs["version"] == 5

    async def test_delete(
        self,
        client_session: ClientSession,
        mock_dashboards_protocol: AsyncMock,
    ) -> None:
        mock_dashboards_protocol.dashboard_delete.return_value = None

        result = await client_session.call_tool(
            "dashboards", {"action": "delete", "dashboard_id": "d1"}
        )

        assert not result.isError


# ─── sprints ────────────────────────────────────────────────


class TestSprints:
    async def test_get(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_sprint: Sprint,
    ) -> None:
        mock_boards_protocol.sprint_get.return_value = sample_sprint

        result = await client_session.call_tool(
            "sprints", {"action": "get", "sprint_id": "44"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["sprint"]["id"] == sample_sprint.id

    async def test_create(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_sprint: Sprint,
    ) -> None:
        mock_boards_protocol.sprint_create.return_value = sample_sprint

        result = await client_session.call_tool(
            "sprints",
            {
                "action": "create",
                "board_id": 73,
                "name": "Sprint 1",
                "start_date": "2026-05-01",
                "end_date": "2026-05-14",
            },
        )

        assert not result.isError
        call_kwargs = mock_boards_protocol.sprint_create.call_args.kwargs
        assert call_kwargs["name"] == "Sprint 1"
        assert call_kwargs["start_date"] == "2026-05-01"

    async def test_update(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_sprint: Sprint,
    ) -> None:
        mock_boards_protocol.sprint_update.return_value = sample_sprint

        result = await client_session.call_tool(
            "sprints",
            {
                "action": "update",
                "sprint_id": 44,
                "fields": {"name": "Renamed"},
            },
        )

        assert not result.isError

    async def test_delete(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        mock_boards_protocol.sprint_delete.return_value = None

        result = await client_session.call_tool(
            "sprints", {"action": "delete", "sprint_id": 44}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content == {"ok": True}

    @pytest.mark.parametrize("action", ["start", "finish"])
    async def test_lifecycle(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_sprint: Sprint,
        action: str,
    ) -> None:
        getattr(mock_boards_protocol, f"sprint_{action}").return_value = sample_sprint

        result = await client_session.call_tool(
            "sprints", {"action": action, "sprint_id": 44}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["sprint"]["id"] == sample_sprint.id

    async def test_read_only_blocks_start(
        self,
        client_session_read_only: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "sprints", {"action": "start", "sprint_id": 44}
        )
        assert result.isError
        mock_boards_protocol.sprint_start.assert_not_called()
