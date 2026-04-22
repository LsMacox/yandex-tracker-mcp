"""Tests for the structured-filter → YQL converter."""

from typing import Any

import pytest

from mcp_tracker.mcp.yql import (
    FilterConversionError,
    filter_to_yql,
    order_to_sort_by,
)


class TestScalars:
    @pytest.mark.parametrize(
        "filter_dict,expected",
        [
            ({"queue": "TEST"}, "Queue: TEST"),
            ({"queue": "test-lower"}, "Queue: test-lower"),
            ({"priority": "normal"}, "Priority: normal"),
            ({"description": "x"}, "Description: x"),
            # Bool and int pass through
            ({"favorite": True}, "favorite: true"),
            ({"story_points": 5}, "StoryPoints: 5"),
        ],
    )
    def test_plain_scalars(self, filter_dict: dict[str, Any], expected: str) -> None:
        assert filter_to_yql(filter_dict) == expected

    def test_values_with_spaces_get_quoted(self) -> None:
        assert filter_to_yql({"board": "My Board"}) == 'Boards: "My Board"'

    def test_values_with_quotes_get_escaped(self) -> None:
        assert filter_to_yql({"summary": 'has "quote"'}) == r'Summary: "has \"quote\""'


class TestMagicValues:
    @pytest.mark.parametrize(
        "raw,rendered",
        [
            ("empty", "empty()"),
            ("notEmpty", "notEmpty()"),
            ("me", "me()"),
            ("today", "today()"),
            ("yesterday", "yesterday()"),
            ("now", "now()"),
            ("resolved", "notEmpty()"),
            ("unresolved", "empty()"),
        ],
    )
    def test_magic(self, raw: str, rendered: str) -> None:
        assert filter_to_yql({"resolution": raw}) == f"Resolution: {rendered}"


class TestLists:
    def test_or_list(self) -> None:
        assert (
            filter_to_yql({"status": ["open", "inProgress"]})
            == "Status: open, inProgress"
        )

    def test_empty_list_rejected(self) -> None:
        with pytest.raises(FilterConversionError):
            filter_to_yql({"status": []})

    def test_list_with_quoted_values(self) -> None:
        assert (
            filter_to_yql({"board": ["My Board", "Other"]})
            == 'Boards: "My Board", Other'
        )


class TestRanges:
    def test_from_to(self) -> None:
        assert (
            filter_to_yql({"created": {"from": "2024-01-01", "to": "2024-12-31"}})
            == "Created: 2024-01-01 .. 2024-12-31"
        )

    def test_gt_only(self) -> None:
        assert filter_to_yql({"created": {"gt": "2024-01-01"}}) == (
            "Created: > 2024-01-01"
        )

    def test_gte_lte_mix(self) -> None:
        assert filter_to_yql(
            {"updated": {"gte": "2024-01-01", "lt": "2024-06-01"}}
        ) == ("(Updated: >= 2024-01-01 AND Updated: < 2024-06-01)")

    def test_empty_range_rejected(self) -> None:
        with pytest.raises(FilterConversionError):
            filter_to_yql({"created": {"foo": "bar"}})


class TestCombined:
    def test_classic_three_clause(self) -> None:
        assert (
            filter_to_yql(
                {"queue": "LOCALIOFFICE", "resolution": "empty", "assignee": "me"}
            )
            == "Queue: LOCALIOFFICE AND Resolution: empty() AND Assignee: me()"
        )

    def test_empty_filter_rejected(self) -> None:
        with pytest.raises(FilterConversionError):
            filter_to_yql({})

    def test_custom_field_passes_through(self) -> None:
        # Unknown key → used as-is (local/custom fields already use their id).
        assert filter_to_yql({"customField123": "foo"}) == "customField123: foo"


class TestOrderToSortBy:
    def test_asc_and_desc(self) -> None:
        assert order_to_sort_by(["-updated", "+priority"]) == (
            '"Sort By": Updated DESC, Priority ASC'
        )

    def test_empty(self) -> None:
        assert order_to_sort_by([]) == ""

    def test_default_ascending(self) -> None:
        assert order_to_sort_by(["created"]) == '"Sort By": Created ASC'
