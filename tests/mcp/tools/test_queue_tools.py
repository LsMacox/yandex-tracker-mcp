from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.fields import GlobalField
from mcp_tracker.tracker.proto.types.queues import Queue, QueueVersion
from tests.mcp.conftest import get_tool_result_content


class TestQueuesList:
    async def test_returns_queues(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
        sample_queues: list[Queue],
    ) -> None:
        mock_queues_protocol.queues_list.side_effect = [sample_queues, []]

        result = await client_session.call_tool("queues", {"action": "list"})

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["queues"]) == len(sample_queues)

    async def test_restricted_filters(
        self,
        client_session_with_limits: ClientSession,
        mock_queues_protocol: AsyncMock,
        sample_queues: list[Queue],
    ) -> None:
        mock_queues_protocol.queues_list.side_effect = [sample_queues, []]

        result = await client_session_with_limits.call_tool(
            "queues", {"action": "list"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        for queue in content["queues"]:
            assert queue["key"] == "ALLOWED"


class TestQueuesTags:
    async def test_tags(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
    ) -> None:
        mock_queues_protocol.queues_get_tags.return_value = ["a", "b"]

        result = await client_session.call_tool(
            "queues", {"action": "tags", "queue_id": "TEST"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content == {"tags": ["a", "b"]}


class TestQueuesVersions:
    async def test_versions(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
    ) -> None:
        mock_queues_protocol.queues_get_versions.return_value = [
            QueueVersion.model_construct(
                id=1, name="1.0", version=1, released=False, archived=False
            ),
        ]

        result = await client_session.call_tool(
            "queues", {"action": "versions", "queue_id": "TEST"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["versions"]) == 1


class TestQueuesFields:
    async def test_fields_global_only(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
    ) -> None:
        mock_queues_protocol.queues_get_fields.return_value = [
            GlobalField.model_construct(id="fa", name="Field A"),
        ]

        result = await client_session.call_tool(
            "queues",
            {
                "action": "fields",
                "queue_id": "TEST",
                "include_local_fields": False,
            },
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["fields"]) == 1
        mock_queues_protocol.queues_get_local_fields.assert_not_called()

    async def test_fields_with_local(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
    ) -> None:
        mock_queues_protocol.queues_get_fields.return_value = [
            GlobalField.model_construct(id="fa", name="Field A"),
        ]
        mock_queues_protocol.queues_get_local_fields.return_value = [
            GlobalField.model_construct(id="fb", name="Field B"),
        ]

        result = await client_session.call_tool(
            "queues", {"action": "fields", "queue_id": "TEST"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["fields"]) == 2


class TestQueuesMetadata:
    async def test_metadata(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
    ) -> None:
        mock_queues_protocol.queue_get.return_value = Queue.model_construct(
            id=1, key="TEST", name="Test"
        )

        result = await client_session.call_tool(
            "queues", {"action": "metadata", "queue_id": "TEST"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["queue"]["key"] == "TEST"


class TestQueuesCreate:
    async def test_create(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
    ) -> None:
        mock_queues_protocol.queue_create.return_value = Queue.model_construct(
            id=1, key="NEW", name="New"
        )

        result = await client_session.call_tool(
            "queues",
            {
                "action": "create",
                "key": "NEW",
                "name": "New",
                "lead": "alice",
            },
        )

        assert not result.isError
        call_kwargs = mock_queues_protocol.queue_create.call_args.kwargs
        assert call_kwargs["key"] == "NEW"
        assert call_kwargs["lead"] == "alice"

    async def test_read_only_blocks(
        self,
        client_session_read_only: ClientSession,
        mock_queues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "queues",
            {
                "action": "create",
                "key": "NEW",
                "name": "New",
                "lead": "alice",
            },
        )
        assert result.isError
        mock_queues_protocol.queue_create.assert_not_called()
