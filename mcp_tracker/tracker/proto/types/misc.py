"""Generic types for filters, components, entities, dashboards, automations."""

from datetime import datetime
from typing import Any

from pydantic import ConfigDict

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity, NoneExcludedField


class _Generic(BaseTrackerEntity):
    """Base generic entity — keeps unknown fields, all optional."""

    model_config = ConfigDict(extra="allow")

    self: str | None = NoneExcludedField
    id: str | int | None = NoneExcludedField
    key: str | None = NoneExcludedField
    version: int | None = NoneExcludedField
    name: str | None = NoneExcludedField
    display: str | None = NoneExcludedField
    description: str | None = NoneExcludedField
    createdAt: datetime | None = NoneExcludedField
    updatedAt: datetime | None = NoneExcludedField


class IssueFilter(_Generic):
    query: str | None = NoneExcludedField
    owner: dict[str, Any] | None = NoneExcludedField


class Component(_Generic):
    queue: dict[str, Any] | None = NoneExcludedField
    lead: dict[str, Any] | None = NoneExcludedField
    assignAuto: bool | None = NoneExcludedField


class Project(_Generic):
    """New-API project entity (/v3/entities/project)."""

    shortId: int | None = NoneExcludedField
    entityStatus: str | None = NoneExcludedField
    fields: dict[str, Any] | None = NoneExcludedField


class Portfolio(_Generic):
    shortId: int | None = NoneExcludedField
    entityStatus: str | None = NoneExcludedField
    fields: dict[str, Any] | None = NoneExcludedField


class Goal(_Generic):
    shortId: int | None = NoneExcludedField
    entityStatus: str | None = NoneExcludedField
    fields: dict[str, Any] | None = NoneExcludedField


class ProjectLegacy(_Generic):
    """Legacy /v2/projects entity, kept for completeness."""


class Dashboard(_Generic):
    owner: dict[str, Any] | None = NoneExcludedField
    access: dict[str, Any] | None = NoneExcludedField


class DashboardWidget(_Generic):
    type: str | None = NoneExcludedField
    settings: dict[str, Any] | None = NoneExcludedField
    boardPosition: dict[str, Any] | None = NoneExcludedField


class Trigger(_Generic):
    queue: dict[str, Any] | None = NoneExcludedField
    actions: list[dict[str, Any]] | None = NoneExcludedField
    conditions: list[dict[str, Any]] | None = NoneExcludedField
    active: bool | None = NoneExcludedField


class Autoaction(_Generic):
    queue: dict[str, Any] | None = NoneExcludedField
    filter: dict[str, Any] | None = NoneExcludedField
    actions: list[dict[str, Any]] | None = NoneExcludedField
    active: bool | None = NoneExcludedField
    cronExpression: str | None = NoneExcludedField


class Macro(_Generic):
    queue: dict[str, Any] | None = NoneExcludedField
    body: str | None = NoneExcludedField
    fieldChanges: list[dict[str, Any]] | None = NoneExcludedField


class WorkflowStep(_Generic):
    type: str | None = NoneExcludedField


class Workflow(_Generic):
    queue: dict[str, Any] | None = NoneExcludedField
    steps: list[WorkflowStep] | None = NoneExcludedField
    initialStatus: dict[str, Any] | None = NoneExcludedField


class BulkChangeResult(BaseTrackerEntity):
    """Polling token returned by bulk endpoints."""

    model_config = ConfigDict(extra="allow")

    id: str | None = NoneExcludedField
    self: str | None = NoneExcludedField
    status: str | None = NoneExcludedField
    createdAt: datetime | None = NoneExcludedField
    updatedAt: datetime | None = NoneExcludedField
    executionChunkPercent: int | None = NoneExcludedField
