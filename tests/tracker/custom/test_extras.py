"""HTTP tests for filters/components/entities/dashboards/automations/bulk/issue-extras."""

import os
import tempfile
from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.types.boards import Board, BoardColumn, Sprint
from mcp_tracker.tracker.proto.types.issues import (
    ChecklistItem,
    Issue,
    IssueAttachment,
    IssueLink,
)
from mcp_tracker.tracker.proto.types.misc import (
    Autoaction,
    BulkChangeResult,
    Component,
    Dashboard,
    DashboardWidget,
    IssueFilter,
    Macro,
    Trigger,
    Workflow,
)


class TestFilters:
    async def test_filters_list(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/filters",
                payload=[{"id": "1", "name": "My filter", "query": "queue: TEST"}],
            )
            result = await tracker_client.filters_list()
        assert len(result) == 1
        assert isinstance(result[0], IssueFilter)

    async def test_filter_create(self, tracker_client: TrackerClient) -> None:
        payload = {"id": "42", "name": "New", "query": "queue: TEST"}
        with aioresponses() as m:
            m.post("https://api.tracker.yandex.net/v3/filters", payload=payload)
            result = await tracker_client.filter_create(name="New", query="queue: TEST")
        assert result.id == "42"

    async def test_filter_delete(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.delete("https://api.tracker.yandex.net/v3/filters/1", status=204)
            await tracker_client.filter_delete("1")


class TestComponents:
    async def test_components_list(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/components?perPage=50&page=1",
                payload=[{"id": 1, "name": "Core"}],
            )
            result = await tracker_client.components_list()
        assert len(result) == 1
        assert isinstance(result[0], Component)

    async def test_component_create(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/components",
                payload={"id": 5, "name": "Back"},
            )
            result = await tracker_client.component_create(name="Back", queue="TEST")
        assert result.id == 5


class TestEntities:
    async def test_projects_search(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/entities/project/_search?perPage=50&page=1",
                payload=[{"id": "p1", "name": "Project 1"}],
            )
            result = await tracker_client.projects_search()
        assert len(result) == 1
        assert result[0].id == "p1"

    async def test_entity_create(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/entities/goal",
                payload={"id": "g1", "fields": {"summary": "Q1"}},
            )
            result = await tracker_client.entity_create(
                "goal", fields={"summary": "Q1"}
            )
        assert result["id"] == "g1"


class TestDashboards:
    async def test_dashboards_list(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/dashboards?perPage=50&page=1",
                payload=[{"id": "d1", "name": "Home"}],
            )
            result = await tracker_client.dashboards_list()
        assert len(result) == 1
        assert isinstance(result[0], Dashboard)

    async def test_dashboard_widgets(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/dashboards/d1/widgets",
                payload=[{"id": "w1", "type": "issueList"}],
            )
            result = await tracker_client.dashboard_get_widgets("d1")
        assert len(result) == 1
        assert isinstance(result[0], DashboardWidget)


class TestAutomations:
    async def test_triggers_list(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST/triggers",
                payload=[{"id": 1, "name": "onCreate"}],
            )
            result = await tracker_client.triggers_list("TEST")
        assert isinstance(result[0], Trigger)

    async def test_autoactions_list(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST/autoactions",
                payload=[{"id": 2, "name": "nightly"}],
            )
            result = await tracker_client.autoactions_list("TEST")
        assert isinstance(result[0], Autoaction)

    async def test_macros_list(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST/macros",
                payload=[{"id": 3, "name": "close"}],
            )
            result = await tracker_client.macros_list("TEST")
        assert isinstance(result[0], Macro)

    async def test_workflows_list(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/workflows",
                payload=[{"id": "wf1", "name": "Kanban"}],
            )
            result = await tracker_client.workflows_list()
        assert isinstance(result[0], Workflow)

    async def test_queue_workflow_get(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST/workflow",
                payload={"id": "wf1", "name": "Kanban"},
            )
            result = await tracker_client.queue_workflow_get("TEST")
        assert isinstance(result, Workflow)


class TestBulkChange:
    async def test_bulk_update(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v2/bulkchange/_update",
                payload={"id": "op1", "status": "CREATED"},
            )
            result = await tracker_client.bulk_update(
                issues=["TEST-1"], values={"priority": "high"}
            )
        assert isinstance(result, BulkChangeResult)
        assert result.id == "op1"

    async def test_bulk_move(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v2/bulkchange/_move",
                payload={"id": "op2", "status": "IN_PROGRESS"},
            )
            result = await tracker_client.bulk_move(issues=["TEST-1"], queue="DEV")
        assert result.id == "op2"

    async def test_bulk_transition(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v2/bulkchange/_transition",
                payload={"id": "op3", "status": "COMPLETED"},
            )
            result = await tracker_client.bulk_transition(
                issues=["TEST-1"], transition="close"
            )
        assert result.id == "op3"


class TestIssueExtras:
    @pytest.fixture
    def sample_issue_payload(self) -> dict[str, Any]:
        return {
            "id": "abc",
            "key": "TEST-1",
            "summary": "Sample",
        }

    async def test_issue_add_link(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-1/links",
                payload={
                    "id": 42,
                    "direction": "outward",
                    "type": {"id": "relates"},
                },
            )
            result = await tracker_client.issue_add_link(
                "TEST-1", relationship="relates", target_issue="TEST-2"
            )
        assert isinstance(result, IssueLink)
        assert result.id == 42

    async def test_issue_delete_link(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/issues/TEST-1/links/42", status=204
            )
            await tracker_client.issue_delete_link("TEST-1", 42)

    async def test_issue_add_checklist_item(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-1/checklistItems",
                payload=[{"id": "c1", "text": "Do it", "checked": False}],
            )
            result = await tracker_client.issue_add_checklist_item(
                "TEST-1", text="Do it"
            )
        assert len(result) == 1
        assert isinstance(result[0], ChecklistItem)

    async def test_issue_add_tags(
        self, tracker_client: TrackerClient, sample_issue_payload: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-1",
                payload={**sample_issue_payload, "tags": ["bug", "urgent"]},
            )
            result = await tracker_client.issue_add_tags("TEST-1", ["urgent"])
        assert isinstance(result, Issue)

    async def test_issue_move_to_queue(
        self, tracker_client: TrackerClient, sample_issue_payload: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-1/_move",
                payload={**sample_issue_payload, "key": "DEV-1"},
            )
            result = await tracker_client.issue_move_to_queue("TEST-1", "DEV")
        assert result.key == "DEV-1"

    async def test_issue_upload_attachment(self, tracker_client: TrackerClient) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as fh:
            fh.write("hello")
            tmp_path = fh.name
        try:
            with aioresponses() as m:
                m.post(
                    "https://api.tracker.yandex.net/v3/issues/TEST-1/attachments",
                    payload={"id": "a1", "name": os.path.basename(tmp_path)},
                )
                result = await tracker_client.issue_upload_attachment(
                    "TEST-1", file_path=tmp_path
                )
            assert isinstance(result, IssueAttachment)
            assert result.id == "a1"
        finally:
            os.unlink(tmp_path)

    async def test_issue_download_attachment(
        self, tracker_client: TrackerClient
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with aioresponses() as m:
                m.get(
                    "https://api.tracker.yandex.net/v3/issues/TEST-1/attachments/a1/hello.txt",
                    body=b"hello world",
                    headers={"Content-Type": "application/octet-stream"},
                )
                dest = await tracker_client.issue_download_attachment(
                    "TEST-1", "a1", "hello.txt", dest_path=tmp_dir
                )
            assert dest.endswith("hello.txt")
            with open(dest, "rb") as fh:
                assert fh.read() == b"hello world"


class TestBoardsWrite:
    async def test_board_create(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/boards",
                payload={"id": 11, "name": "New"},
            )
            result = await tracker_client.board_create(name="New")
        assert isinstance(result, Board)

    async def test_board_update(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/boards/7",
                payload={"id": 7, "name": "Renamed"},
            )
            result = await tracker_client.board_update(7, fields={"name": "Renamed"})
        assert result.name == "Renamed"

    async def test_board_delete(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.delete("https://api.tracker.yandex.net/v3/boards/7", status=204)
            await tracker_client.board_delete(7)

    async def test_column_create(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/boards/7/columns/",
                payload={"id": 1, "name": "Open"},
            )
            result = await tracker_client.board_column_create(
                7, name="Open", statuses=["open"]
            )
        assert isinstance(result, BoardColumn)

    async def test_sprint_create(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/boards/7/sprints",
                payload={"id": 55, "name": "Sprint A", "status": "draft"},
            )
            result = await tracker_client.sprint_create(7, name="Sprint A")
        assert isinstance(result, Sprint)
        assert result.id == 55
