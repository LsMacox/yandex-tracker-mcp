from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.users import User
from tests.mcp.conftest import get_tool_result_content


class TestUsersList:
    async def test_list(
        self,
        client_session: ClientSession,
        mock_users_protocol: AsyncMock,
        sample_users: list[User],
    ) -> None:
        mock_users_protocol.users_list.return_value = sample_users

        result = await client_session.call_tool("users", {"action": "list"})

        assert not result.isError
        mock_users_protocol.users_list.assert_called_once()
        content = get_tool_result_content(result)
        items = content["users"]
        assert len(items) == len(sample_users)
        assert items[0]["login"] == sample_users[0].login


class TestUsersSearch:
    async def test_exact_login_match(
        self,
        client_session: ClientSession,
        mock_users_protocol: AsyncMock,
        sample_users: list[User],
    ) -> None:
        mock_users_protocol.users_list.side_effect = [sample_users, []]

        result = await client_session.call_tool(
            "users",
            {"action": "search", "query": sample_users[0].login},
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["users"]) == 1
        assert content["users"][0]["login"] == sample_users[0].login

    async def test_no_match_returns_empty(
        self,
        client_session: ClientSession,
        mock_users_protocol: AsyncMock,
        sample_users: list[User],
    ) -> None:
        mock_users_protocol.users_list.side_effect = [sample_users, []]

        result = await client_session.call_tool(
            "users", {"action": "search", "query": "zzz-unknown-query"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["users"] == []


class TestUsersGet:
    async def test_get(
        self,
        client_session: ClientSession,
        mock_users_protocol: AsyncMock,
        sample_users: list[User],
    ) -> None:
        mock_users_protocol.user_get.return_value = sample_users[0]

        result = await client_session.call_tool(
            "users", {"action": "get", "user_id": sample_users[0].login}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["user"]["login"] == sample_users[0].login

    async def test_get_not_found(
        self,
        client_session: ClientSession,
        mock_users_protocol: AsyncMock,
    ) -> None:
        mock_users_protocol.user_get.return_value = None

        result = await client_session.call_tool(
            "users", {"action": "get", "user_id": "ghost"}
        )

        assert result.isError


class TestUsersCurrent:
    async def test_current(
        self,
        client_session: ClientSession,
        mock_users_protocol: AsyncMock,
        sample_users: list[User],
    ) -> None:
        mock_users_protocol.user_get_current.return_value = sample_users[0]

        result = await client_session.call_tool("users", {"action": "current"})

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["user"]["login"] == sample_users[0].login
