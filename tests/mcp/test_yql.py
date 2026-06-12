"""Tests for the structured-filter → YQL converter."""

from typing import Any

import pytest

from mcp_tracker.mcp.yql import (
    FilterConversionError,
    filter_to_yql,
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
            ("resolved", "notEmpty()"),
            ("unresolved", "empty()"),
        ],
    )
    def test_resolution_magic(self, raw: str, rendered: str) -> None:
        assert filter_to_yql({"resolution": raw}) == f"Resolution: {rendered}"

    @pytest.mark.parametrize(
        "field,raw,rendered",
        [
            ("assignee", "me", "me()"),
            ("author", "me", "me()"),
            ("created", "today", "today()"),
            ("updated", "yesterday", "yesterday()"),
            ("resolved", "now", "now()"),
            ("created", "week", "week()"),
        ],
    )
    def test_field_scoped_magic(self, field: str, raw: str, rendered: str) -> None:
        yql_field = filter_to_yql({field: raw}).split(":")[0]
        assert filter_to_yql({field: raw}) == f"{yql_field}: {rendered}"

    @pytest.mark.parametrize(
        "filter_dict,expected",
        [
            # `resolved` is a legit status key — must stay a literal.
            ({"status": "resolved"}, "Status: resolved"),
            ({"status": ["open", "resolved"]}, "Status: open, resolved"),
            # Date functions must not hijack values of non-date fields.
            ({"tags": "today"}, "Tags: today"),
            ({"summary": "week"}, "Summary: week"),
            # `me` only applies to user fields.
            ({"summary": "me"}, "Summary: me"),
        ],
    )
    def test_magic_does_not_hijack_literals(
        self, filter_dict: dict[str, Any], expected: str
    ) -> None:
        assert filter_to_yql(filter_dict) == expected

    def test_generic_empty_applies_to_any_field(self) -> None:
        assert filter_to_yql({"tags": "empty"}) == "Tags: empty()"


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
