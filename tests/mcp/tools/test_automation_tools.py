"""Tests for consolidated automation tools: triggers/autoactions/macros/workflows."""

from unittest.mock import AsyncMock

import pytest
from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.misc import (
    Autoaction,
    Macro,
    Trigger,
    Workflow,
)
from tests.mcp.conftest import get_tool_result_content


@pytest.fixture
def sample_trigger() -> Trigger:
    return Trigger.model_construct(id=1, name="Auto Assign", active=True)


@pytest.fixture
def sample_triggers(sample_trigger: Trigger) -> list[Trigger]:
    return [sample_trigger]


@pytest.fixture
def sample_autoaction() -> Autoaction:
    return Autoaction.model_construct(id=1, name="Nightly", active=True)


@pytest.fixture
def sample_autoactions(sample_autoaction: Autoaction) -> list[Autoaction]:
    return [sample_autoaction]


@pytest.fixture
def sample_macro() -> Macro:
    return Macro.model_construct(id=1, name="Close as duplicate")


@pytest.fixture
def sample_macros(sample_macro: Macro) -> list[Macro]:
    return [sample_macro]


@pytest.fixture
def sample_workflow() -> Workflow:
    return Workflow.model_construct(id="wf1", name="Default")


class TestTriggers:
    async def test_list(
        self,
        client_session: ClientSession,
        mock_automations_protocol: AsyncMock,
        sample_triggers: list[Trigger],
    ) -> None:
        mock_automations_protocol.triggers_list.return_value = sample_triggers

        result = await client_session.call_tool(
            "triggers", {"action": "list", "queue_id": "TEST"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["triggers"]) == len(sample_triggers)

    async def test_get(
        self,
        client_session: ClientSession,
        mock_automations_protocol: AsyncMock,
        sample_trigger: Trigger,
    ) -> None:
        mock_automations_protocol.trigger_get.return_value = sample_trigger

        result = await client_session.call_tool(
            "triggers",
            {"action": "get", "queue_id": "TEST", "trigger_id": 1},
        )

        assert not result.isError

    async def test_create(
        self,
        client_session: ClientSession,
        mock_automations_protocol: AsyncMock,
        sample_trigger: Trigger,
    ) -> None:
        mock_automations_protocol.trigger_create.return_value = sample_trigger

        result = await client_session.call_tool(
            "triggers",
            {
                "action": "create",
                "queue_id": "TEST",
                "name": "Auto",
                "actions": [{"type": "set", "field": "assignee"}],
            },
        )

        assert not result.isError

    async def test_delete(
        self,
        client_session: ClientSession,
        mock_automations_protocol: AsyncMock,
    ) -> None:
        mock_automations_protocol.trigger_delete.return_value = None

        result = await client_session.call_tool(
            "triggers",
            {"action": "delete", "queue_id": "TEST", "trigger_id": 1},
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content == {"ok": True}

    async def test_read_only_blocks_create(
        self,
        client_session_read_only: ClientSession,
        mock_automations_protocol: AsyncMock,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "triggers",
            {
                "action": "create",
                "queue_id": "TEST",
                "name": "x",
                "actions": [],
            },
        )
        assert result.isError
        mock_automations_protocol.trigger_create.assert_not_called()


class TestAutoactions:
    async def test_list(
        self,
        client_session: ClientSession,
        mock_automations_protocol: AsyncMock,
        sample_autoactions: list[Autoaction],
    ) -> None:
        mock_automations_protocol.autoactions_list.return_value = sample_autoactions

        result = await client_session.call_tool(
            "autoactions", {"action": "list", "queue_id": "TEST"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["autoactions"]) == len(sample_autoactions)

    async def test_create(
        self,
        client_session: ClientSession,
        mock_automations_protocol: AsyncMock,
        sample_autoaction: Autoaction,
    ) -> None:
        mock_automations_protocol.autoaction_create.return_value = sample_autoaction

        result = await client_session.call_tool(
            "autoactions",
            {
                "action": "create",
                "queue_id": "TEST",
                "name": "Nightly",
                "filter": {"status": "open"},
                "actions": [{"type": "close"}],
            },
        )

        assert not result.isError


class TestMacros:
    async def test_list(
        self,
        client_session: ClientSession,
        mock_automations_protocol: AsyncMock,
        sample_macros: list[Macro],
    ) -> None:
        mock_automations_protocol.macros_list.return_value = sample_macros

        result = await client_session.call_tool(
            "macros", {"action": "list", "queue_id": "TEST"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["macros"]) == len(sample_macros)

    async def test_create(
        self,
        client_session: ClientSession,
        mock_automations_protocol: AsyncMock,
        sample_macro: Macro,
    ) -> None:
        mock_automations_protocol.macro_create.return_value = sample_macro

        result = await client_session.call_tool(
            "macros",
            {
                "action": "create",
                "queue_id": "TEST",
                "name": "Close dup",
                "body": "Duplicate of {{key}}",
            },
        )

        assert not result.isError


class TestWorkflows:
    async def test_list(
        self,
        client_session: ClientSession,
        mock_automations_protocol: AsyncMock,
        sample_workflow: Workflow,
    ) -> None:
        mock_automations_protocol.workflows_list.return_value = [sample_workflow]

        result = await client_session.call_tool("workflows", {"action": "list"})

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["workflows"]) == 1

    async def test_get_queue(
        self,
        client_session: ClientSession,
        mock_automations_protocol: AsyncMock,
        sample_workflow: Workflow,
    ) -> None:
        mock_automations_protocol.queue_workflow_get.return_value = sample_workflow

        result = await client_session.call_tool(
            "workflows", {"action": "get_queue", "queue_id": "TEST"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["workflow"]["id"] == sample_workflow.id

    async def test_get_queue_none(
        self,
        client_session: ClientSession,
        mock_automations_protocol: AsyncMock,
    ) -> None:
        mock_automations_protocol.queue_workflow_get.return_value = None

        result = await client_session.call_tool(
            "workflows", {"action": "get_queue", "queue_id": "TEST"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["workflow"] is None
