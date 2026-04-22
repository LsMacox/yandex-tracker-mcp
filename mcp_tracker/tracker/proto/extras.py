"""Protocols for extra domains: filters, components, entities, dashboards,
automations (triggers/autoactions/macros/workflows), bulk change."""

from typing import Any, Protocol, runtime_checkable

from .common import YandexAuth
from .types.misc import (
    Autoaction,
    BulkChangeResult,
    Component,
    Dashboard,
    DashboardWidget,
    Goal,
    IssueFilter,
    Macro,
    Portfolio,
    Project,
    ProjectLegacy,
    Trigger,
    Workflow,
)


@runtime_checkable
class FiltersProtocol(Protocol):
    async def filters_list(
        self, *, auth: YandexAuth | None = None
    ) -> list[IssueFilter]: ...

    async def filter_get(
        self, filter_id: str, *, auth: YandexAuth | None = None
    ) -> IssueFilter: ...

    async def filter_create(
        self,
        *,
        name: str,
        query: str,
        owner: str | dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
        auth: YandexAuth | None = None,
    ) -> IssueFilter: ...

    async def filter_update(
        self,
        filter_id: str,
        *,
        fields: dict[str, Any],
        auth: YandexAuth | None = None,
    ) -> IssueFilter: ...

    async def filter_delete(
        self, filter_id: str, *, auth: YandexAuth | None = None
    ) -> None: ...


class FiltersProtocolWrap(FiltersProtocol):
    def __init__(self, original: FiltersProtocol) -> None:
        self._original = original


@runtime_checkable
class ComponentsProtocol(Protocol):
    async def components_list(
        self,
        *,
        per_page: int = 50,
        page: int = 1,
        auth: YandexAuth | None = None,
    ) -> list[Component]: ...

    async def component_get(
        self, component_id: str | int, *, auth: YandexAuth | None = None
    ) -> Component: ...

    async def component_create(
        self,
        *,
        name: str,
        queue: str,
        description: str | None = None,
        lead: str | None = None,
        assign_auto: bool | None = None,
        extra: dict[str, Any] | None = None,
        auth: YandexAuth | None = None,
    ) -> Component: ...

    async def component_update(
        self,
        component_id: str | int,
        *,
        fields: dict[str, Any],
        auth: YandexAuth | None = None,
    ) -> Component: ...

    async def component_delete(
        self, component_id: str | int, *, auth: YandexAuth | None = None
    ) -> None: ...


class ComponentsProtocolWrap(ComponentsProtocol):
    def __init__(self, original: ComponentsProtocol) -> None:
        self._original = original


@runtime_checkable
class EntitiesProtocol(Protocol):
    """Projects / portfolios / goals (new /v3/entities/ API)."""

    async def entities_search(
        self,
        entity_type: str,
        *,
        filter: dict[str, Any] | None = None,
        order: list[str] | None = None,
        per_page: int = 50,
        page: int = 1,
        fields: list[str] | None = None,
        root_only: bool | None = None,
        expand: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> list[dict[str, Any]]: ...

    async def entity_get(
        self,
        entity_type: str,
        entity_id: str,
        *,
        fields: list[str] | None = None,
        expand: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> dict[str, Any]: ...

    async def entity_create(
        self,
        entity_type: str,
        *,
        fields: dict[str, Any],
        auth: YandexAuth | None = None,
    ) -> dict[str, Any]: ...

    async def entity_update(
        self,
        entity_type: str,
        entity_id: str,
        *,
        fields: dict[str, Any],
        auth: YandexAuth | None = None,
    ) -> dict[str, Any]: ...

    async def entity_delete(
        self,
        entity_type: str,
        entity_id: str,
        *,
        auth: YandexAuth | None = None,
    ) -> None: ...

    # typed helpers
    async def projects_search(
        self,
        *,
        filter: dict[str, Any] | None = None,
        order: list[str] | None = None,
        per_page: int = 50,
        page: int = 1,
        auth: YandexAuth | None = None,
    ) -> list[Project]: ...

    async def portfolios_search(
        self,
        *,
        filter: dict[str, Any] | None = None,
        order: list[str] | None = None,
        per_page: int = 50,
        page: int = 1,
        auth: YandexAuth | None = None,
    ) -> list[Portfolio]: ...

    async def goals_search(
        self,
        *,
        filter: dict[str, Any] | None = None,
        order: list[str] | None = None,
        per_page: int = 50,
        page: int = 1,
        auth: YandexAuth | None = None,
    ) -> list[Goal]: ...

    async def projects_legacy_list(
        self,
        *,
        per_page: int = 50,
        page: int = 1,
        auth: YandexAuth | None = None,
    ) -> list[ProjectLegacy]: ...


class EntitiesProtocolWrap(EntitiesProtocol):
    def __init__(self, original: EntitiesProtocol) -> None:
        self._original = original


@runtime_checkable
class DashboardsProtocol(Protocol):
    async def dashboards_list(
        self,
        *,
        per_page: int = 50,
        page: int = 1,
        auth: YandexAuth | None = None,
    ) -> list[Dashboard]: ...

    async def dashboard_get(
        self, dashboard_id: str, *, auth: YandexAuth | None = None
    ) -> Dashboard: ...

    async def dashboard_get_widgets(
        self, dashboard_id: str, *, auth: YandexAuth | None = None
    ) -> list[DashboardWidget]: ...

    async def dashboard_create(
        self,
        *,
        name: str,
        fields: dict[str, Any] | None = None,
        auth: YandexAuth | None = None,
    ) -> Dashboard: ...

    async def dashboard_update(
        self,
        dashboard_id: str,
        *,
        fields: dict[str, Any],
        auth: YandexAuth | None = None,
    ) -> Dashboard: ...

    async def dashboard_delete(
        self, dashboard_id: str, *, auth: YandexAuth | None = None
    ) -> None: ...


class DashboardsProtocolWrap(DashboardsProtocol):
    def __init__(self, original: DashboardsProtocol) -> None:
        self._original = original


@runtime_checkable
class AutomationsProtocol(Protocol):
    # triggers (queue scoped)
    async def triggers_list(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[Trigger]: ...

    async def trigger_get(
        self, queue_id: str, trigger_id: str | int, *, auth: YandexAuth | None = None
    ) -> Trigger: ...

    async def trigger_create(
        self,
        queue_id: str,
        *,
        name: str,
        actions: list[dict[str, Any]],
        conditions: list[dict[str, Any]] | None = None,
        active: bool | None = None,
        extra: dict[str, Any] | None = None,
        auth: YandexAuth | None = None,
    ) -> Trigger: ...

    async def trigger_update(
        self,
        queue_id: str,
        trigger_id: str | int,
        *,
        fields: dict[str, Any],
        auth: YandexAuth | None = None,
    ) -> Trigger: ...

    async def trigger_delete(
        self,
        queue_id: str,
        trigger_id: str | int,
        *,
        auth: YandexAuth | None = None,
    ) -> None: ...

    # autoactions (queue scoped)
    async def autoactions_list(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[Autoaction]: ...

    async def autoaction_get(
        self, queue_id: str, action_id: str | int, *, auth: YandexAuth | None = None
    ) -> Autoaction: ...

    async def autoaction_create(
        self,
        queue_id: str,
        *,
        name: str,
        filter: dict[str, Any],
        actions: list[dict[str, Any]],
        cron_expression: str | None = None,
        active: bool | None = None,
        extra: dict[str, Any] | None = None,
        auth: YandexAuth | None = None,
    ) -> Autoaction: ...

    async def autoaction_update(
        self,
        queue_id: str,
        action_id: str | int,
        *,
        fields: dict[str, Any],
        auth: YandexAuth | None = None,
    ) -> Autoaction: ...

    async def autoaction_delete(
        self,
        queue_id: str,
        action_id: str | int,
        *,
        auth: YandexAuth | None = None,
    ) -> None: ...

    # macros (queue scoped)
    async def macros_list(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[Macro]: ...

    async def macro_get(
        self, queue_id: str, macro_id: str | int, *, auth: YandexAuth | None = None
    ) -> Macro: ...

    async def macro_create(
        self,
        queue_id: str,
        *,
        name: str,
        body: str | None = None,
        field_changes: list[dict[str, Any]] | None = None,
        extra: dict[str, Any] | None = None,
        auth: YandexAuth | None = None,
    ) -> Macro: ...

    async def macro_update(
        self,
        queue_id: str,
        macro_id: str | int,
        *,
        fields: dict[str, Any],
        auth: YandexAuth | None = None,
    ) -> Macro: ...

    async def macro_delete(
        self,
        queue_id: str,
        macro_id: str | int,
        *,
        auth: YandexAuth | None = None,
    ) -> None: ...

    # workflows (read only)
    async def workflows_list(
        self, *, auth: YandexAuth | None = None
    ) -> list[Workflow]: ...

    async def queue_workflow_get(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> Workflow: ...


class AutomationsProtocolWrap(AutomationsProtocol):
    def __init__(self, original: AutomationsProtocol) -> None:
        self._original = original


@runtime_checkable
class BulkChangeProtocol(Protocol):
    async def bulk_update(
        self,
        *,
        issues: list[str],
        values: dict[str, Any],
        comment: str | None = None,
        notify: bool | None = None,
        auth: YandexAuth | None = None,
    ) -> BulkChangeResult: ...

    async def bulk_move(
        self,
        *,
        issues: list[str],
        queue: str,
        move_all_fields: bool | None = None,
        initial_status: bool | None = None,
        notify: bool | None = None,
        extra: dict[str, Any] | None = None,
        auth: YandexAuth | None = None,
    ) -> BulkChangeResult: ...

    async def bulk_transition(
        self,
        *,
        issues: list[str],
        transition: str,
        comment: str | None = None,
        resolution: str | None = None,
        fields: dict[str, Any] | None = None,
        auth: YandexAuth | None = None,
    ) -> BulkChangeResult: ...

    async def bulk_status_get(
        self, operation_id: str, *, auth: YandexAuth | None = None
    ) -> BulkChangeResult: ...


class BulkChangeProtocolWrap(BulkChangeProtocol):
    def __init__(self, original: BulkChangeProtocol) -> None:
        self._original = original
