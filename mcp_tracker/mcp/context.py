from dataclasses import dataclass

from mcp_tracker.tracker.proto.boards import BoardsProtocol
from mcp_tracker.tracker.proto.extras import (
    AutomationsProtocol,
    BulkChangeProtocol,
    ComponentsProtocol,
    DashboardsProtocol,
    EntitiesProtocol,
    FiltersProtocol,
)
from mcp_tracker.tracker.proto.fields import GlobalDataProtocol
from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.users import UsersProtocol


@dataclass
class AppContext:
    queues: QueuesProtocol
    issues: IssueProtocol
    fields: GlobalDataProtocol
    users: UsersProtocol
    boards: BoardsProtocol
    filters: FiltersProtocol
    components: ComponentsProtocol
    entities: EntitiesProtocol
    dashboards: DashboardsProtocol
    automations: AutomationsProtocol
    bulkchange: BulkChangeProtocol
