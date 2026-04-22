from datetime import date, datetime
from typing import Any, Literal

from pydantic import ConfigDict

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity, NoneExcludedField


class BoardColumnStatus(BaseTrackerEntity):
    """Status reference attached to a board column."""

    model_config = ConfigDict(extra="ignore")

    self: str | None = NoneExcludedField
    id: str | None = NoneExcludedField
    key: str | None = NoneExcludedField
    display: str | None = NoneExcludedField


class BoardColumn(BaseTrackerEntity):
    """Column on an agile board."""

    model_config = ConfigDict(extra="ignore")

    self: str | None = NoneExcludedField
    id: int | None = NoneExcludedField
    name: str | None = NoneExcludedField
    statuses: list[BoardColumnStatus] | None = NoneExcludedField


class BoardCreator(BaseTrackerEntity):
    """User reference returned in board/sprint payloads."""

    model_config = ConfigDict(extra="ignore")

    self: str | None = NoneExcludedField
    id: str | None = NoneExcludedField
    display: str | None = NoneExcludedField
    passportUid: int | None = NoneExcludedField
    cloudUid: str | None = NoneExcludedField


class BoardCalendar(BaseTrackerEntity):
    """Calendar reference used for burndown charts."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = NoneExcludedField
    self: str | None = NoneExcludedField


class BoardReference(BaseTrackerEntity):
    """Lightweight board reference embedded into sprint objects."""

    model_config = ConfigDict(extra="ignore")

    self: str | None = NoneExcludedField
    id: int | None = NoneExcludedField
    display: str | None = NoneExcludedField


class Board(BaseTrackerEntity):
    """Agile board returned by Yandex Tracker."""

    model_config = ConfigDict(extra="ignore")

    self: str | None = NoneExcludedField
    id: int | None = NoneExcludedField
    version: int | None = NoneExcludedField
    name: str | None = NoneExcludedField
    createdAt: datetime | None = NoneExcludedField
    updatedAt: datetime | None = NoneExcludedField
    createdBy: BoardCreator | None = NoneExcludedField
    columns: list[BoardColumn] | None = NoneExcludedField
    calendar: BoardCalendar | None = NoneExcludedField
    useRanking: bool | None = NoneExcludedField
    autoFilterSettings: dict[str, Any] | None = NoneExcludedField


SprintStatus = Literal["draft", "in_progress", "released", "archived"]


class Sprint(BaseTrackerEntity):
    """Sprint on an agile board."""

    model_config = ConfigDict(extra="ignore")

    self: str | None = NoneExcludedField
    id: int | None = NoneExcludedField
    version: int | None = NoneExcludedField
    name: str | None = NoneExcludedField
    status: SprintStatus | None = NoneExcludedField
    archived: bool | None = NoneExcludedField
    startDate: date | None = NoneExcludedField
    endDate: date | None = NoneExcludedField
    startDateTime: datetime | None = NoneExcludedField
    endDateTime: datetime | None = NoneExcludedField
    createdAt: datetime | None = NoneExcludedField
    updatedAt: datetime | None = NoneExcludedField
    createdBy: BoardCreator | None = NoneExcludedField
    board: BoardReference | None = NoneExcludedField
