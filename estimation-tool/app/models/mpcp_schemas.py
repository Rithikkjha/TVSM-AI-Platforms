"""Pydantic models for the MPCP Project Tracker module.

Defines all enums, core data models, request/response schemas,
and constants for Managing Points, Check Points, Projects,
Process Track, Execution Track, RAG Status, Dependencies, and Budget.
"""

from datetime import date, datetime
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# =============================================================================
# CONSTANTS
# =============================================================================

VALID_VENDORS: List[str] = [
    "Exathought",
    "Deloitte",
    "TVSD",
    "Evontech",
    "Autovyn",
]

VALID_PRODUCT_OWNERS: List[str] = [
    "Ashish Thakur",
    "Akshay Bhosle",
    "Prakash Bharati",
    "Avinash Kumar",
    "Bibin",
    "Sumitra Rathod",
]

PROCESS_STAGES_ORDERED: List[str] = [
    "BRD",
    "PRD",
    "RFP",
    "PO",
    "Kickoff",
    "Execution_Start",
    "Rolled_Out_To_Prod",
    "Success_Failure",
]

MP_THEME_NAMES: Dict[str, str] = {
    "A": "Customer Satisfaction",
    "B": "Profit & Profitability",
    "C": "Business Growth",
    "D": "New Product Development",
    "E": "Effectiveness of People & System",
    "F": "Digitalization & AI",
    "Z": "Others (Non-MPCP)",
}


# =============================================================================
# ENUMS
# =============================================================================


class MPTheme(str, Enum):
    """MP Theme categories for Managing Point classification."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    Z = "Z"


class BusinessUnit(str, Enum):
    """Business unit / Line of Business classification."""
    IND_2W = "IND-2W"
    CMB_3W = "3W/CMB"
    IB = "IB"


class RAGStatus(str, Enum):
    """Universal RAG health indicator."""
    GREEN = "Green"
    YELLOW = "Yellow"
    RED = "Red"


class RAGSeverity(IntEnum):
    """Numeric severity for RAG comparison."""
    GREEN = 0
    YELLOW = 1
    RED = 2


class ProjectType(str, Enum):
    """Project classification type."""
    FIXED_BID = "Fixed_Bid"
    SPECIAL = "Special"
    BUG = "Bug"
    ENHANCEMENT = "Enhancement"


class ProcessStage(str, Enum):
    """The 8 lifecycle stages in the Process/SOP Track."""
    BRD = "BRD"
    PRD = "PRD"
    RFP = "RFP"
    PO = "PO"
    KICKOFF = "Kickoff"
    EXECUTION_START = "Execution_Start"
    ROLLED_OUT_TO_PROD = "Rolled_Out_To_Prod"
    SUCCESS_FAILURE = "Success_Failure"


class StageStatus(str, Enum):
    """Status of a process track stage."""
    NOT_STARTED = "Not_Started"
    IN_PROGRESS = "In_Progress"
    COMPLETED = "Completed"
    SKIPPED = "Skipped"


class TrackerDomain(str, Enum):
    """Business domain grouping for projects."""
    ALL = "All"
    SHOP = "Shop"
    BUY = "Buy"
    OWN = "Own"
    PARTS = "Parts"


class TrackerStream(str, Enum):
    """Business stream / delivery channel."""
    ALL = "All"
    D2C = "D2C"
    CHANNEL_PARTNER = "Channel Partner"
    PLATFORM_SERVICES = "Platform Services"


class DependencyStatus(str, Enum):
    """Status of an external dependency."""
    OPEN = "Open"
    WIP = "WIP"
    RESOLVED = "Resolved"
    ESCALATED = "Escalated"


class TargetQuarter(str, Enum):
    """Target quarter for a Check Point."""
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"


class BudgetTransactionType(str, Enum):
    """Type of budget transaction."""
    PO_ISSUED = "PO_Issued"
    CHANGE_REQUEST = "Change_Request"
    SPEND = "Spend"
    REFUND = "Refund"


# =============================================================================
# CORE DATA MODELS
# =============================================================================


class RAGContext(BaseModel):
    """3W1H context entry — multiple can exist per entity."""
    id: Optional[str] = Field(None, description="Unique ID for this entry")
    what: Optional[str] = Field(None, description="Description of the issue")
    why: Optional[str] = Field(None, description="Root cause of the issue")
    who: Optional[str] = Field(None, description="Person or team responsible/blocking")
    owner_team: Optional[str] = Field(None, description="Action owner / team who will resolve")
    how: Optional[str] = Field(None, description="Action plan to resolve")
    eta: Optional[date] = Field(None, description="Expected resolution date")
    created_at: Optional[str] = Field(None, description="When this entry was created")
    status: Optional[str] = Field(default="Open", description="Open or Resolved")


class ManagingPoint(BaseModel):
    """A top-level organizational unit in the MPCP hierarchy."""
    id: str = Field(..., description="Unique identifier")
    code: str = Field(..., description="MP code (e.g., A3, B1)")
    name: str = Field(..., description="Managing Point name")
    theme: MPTheme = Field(..., description="MP Theme category (A-F)")
    owner: str = Field(..., description="MP owner name")
    lob: BusinessUnit = Field(..., description="Line of Business")
    bu: BusinessUnit = Field(..., description="Business Unit")
    uom: Optional[str] = Field(None, description="Unit of Measure (e.g., Service NPS Score, %, # Retail 000s MA)")
    target_from: Optional[str] = Field(None, description="Baseline/current value")
    target_to: Optional[str] = Field(None, description="Target value for the FY")
    rag_status: RAGStatus = Field(default=RAGStatus.GREEN)
    rag_context: Optional[RAGContext] = None
    propagated_rag: Optional[RAGStatus] = None
    cp_count: int = Field(default=0)
    project_count: int = Field(default=0)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    created_by: Optional[str] = None


class CheckPoint(BaseModel):
    """A granular grouping under a Managing Point."""
    id: str = Field(...)
    code: str = Field(..., description="CP code (e.g., A3.1, B1.4)")
    name: str = Field(...)
    owner: str = Field(...)
    description: Optional[str] = None
    domain: Optional[TrackerDomain] = None
    stream: Optional[TrackerStream] = None
    uom: Optional[str] = Field(None, description="Unit of Measure")
    target_from: Optional[str] = Field(None, description="Baseline/current value")
    target_to: Optional[str] = Field(None, description="Target value for the FY")
    target_quarter: Optional[TargetQuarter] = None
    parent_mp_id: str = Field(...)
    rag_status: RAGStatus = Field(default=RAGStatus.GREEN)
    rag_context: Optional[RAGContext] = None
    propagated_rag: Optional[RAGStatus] = None
    project_count: int = Field(default=0)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    created_by: Optional[str] = None


class Project(BaseModel):
    """A tracked work item under a Check Point."""
    id: str = Field(...)
    name: str = Field(...)
    project_type: Optional[ProjectType] = None
    vendor: Optional[str] = None
    product_owner: Optional[str] = None
    engg_poc: Optional[str] = Field(None, description="TVSM Engineering POC(s), comma-separated")
    lob: Optional[BusinessUnit] = None
    bu: Optional[BusinessUnit] = None
    domain: Optional[TrackerDomain] = None
    stream: Optional[TrackerStream] = None
    description: Optional[str] = None
    parent_cp_id: str = Field(...)
    rag_status: RAGStatus = Field(default=RAGStatus.GREEN)
    rag_context: Optional[RAGContext] = None
    current_stage: Optional[ProcessStage] = None
    revised_target_date: Optional[date] = None
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    created_by: Optional[str] = None


class ProcessTrackStage(BaseModel):
    """A single stage in a project's process track."""
    project_id: str
    stage: ProcessStage
    stage_order: int = Field(..., ge=0, le=7)
    status: StageStatus = Field(default=StageStatus.NOT_STARTED)
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    remarks: Optional[str] = None
    skip_reason: Optional[str] = None


class ExecutionMilestone(BaseModel):
    """A milestone in a project's execution track."""
    id: str = Field(...)
    project_id: str = Field(...)
    name: str = Field(...)
    vendor: Optional[str] = Field(default="")
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    slippage_days: Optional[int] = None
    is_delayed: bool = False
    rag_status: RAGStatus = Field(default=RAGStatus.GREEN)
    rag_context: List[RAGContext] = Field(default_factory=list)
    remarks: Optional[str] = None


class Dependency(BaseModel):
    """An external dependency linked to a project or milestone."""
    id: str = Field(...)
    project_id: str = Field(...)
    milestone_id: Optional[str] = None
    description: str = Field(...)
    external_owner: str = Field(...)
    cutoff_date: date = Field(...)
    raised_date: date = Field(...)
    status: DependencyStatus = Field(default=DependencyStatus.OPEN)
    resolved_date: Optional[date] = None
    escalation_note: Optional[str] = None
    is_overdue: bool = False
    is_blocker: bool = Field(default=False, description="True if this dependency is blocking project progress")


class BudgetTransaction(BaseModel):
    """A single transaction in the budget ledger."""
    id: str = Field(...)
    transaction_type: BudgetTransactionType
    po_number: Optional[str] = None
    vendor: Optional[str] = None
    amount: float = Field(...)
    date: date  # type: ignore[assignment]
    quarter: Optional[str] = Field(None, description="Quarter tag: Q1, Q2, Q3, Q4")
    remarks: Optional[str] = None


class BudgetData(BaseModel):
    """Budget information for a project (ledger-based)."""
    project_id: str = Field(...)
    approved_budget: float = Field(default=0.0)
    internal_estimate: float = Field(default=0.0)
    quarterly_plan: Dict[str, float] = Field(default_factory=lambda: {"Q1": 0.0, "Q2": 0.0, "Q3": 0.0, "Q4": 0.0}, description="Planned budget allocation per quarter")
    transactions: List[BudgetTransaction] = Field(default_factory=list)
    # Computed fields
    total_committed: float = Field(default=0.0)  # Sum of PO_Issued + Change_Request amounts
    total_spent: float = Field(default=0.0)  # Sum of Spend amounts
    remaining: float = Field(default=0.0)  # approved_budget - total_spent
    remarks: Optional[str] = None


class RAGHistoryEntry(BaseModel):
    """A single entry in the RAG change history."""
    entity_type: str
    entity_id: str
    previous_status: RAGStatus
    new_status: RAGStatus
    rag_context: Optional[RAGContext] = None
    changed_by: str
    timestamp: datetime


# =============================================================================
# REQUEST MODELS
# =============================================================================


class MPCreateRequest(BaseModel):
    """Request to create a Managing Point."""
    code: str = Field(..., min_length=1, description="MP code e.g. A3, B1")
    name: str = Field(..., min_length=1)
    theme: MPTheme
    owner: str = Field(..., min_length=1)
    lob: BusinessUnit
    bu: BusinessUnit
    uom: Optional[str] = None
    target_from: Optional[str] = None
    target_to: Optional[str] = None


class MPUpdateRequest(BaseModel):
    """Request to update a Managing Point."""
    code: Optional[str] = Field(None, min_length=1)
    name: Optional[str] = Field(None, min_length=1)
    theme: Optional[MPTheme] = None
    owner: Optional[str] = Field(None, min_length=1)
    lob: Optional[BusinessUnit] = None
    bu: Optional[BusinessUnit] = None
    uom: Optional[str] = None
    target_from: Optional[str] = None
    target_to: Optional[str] = None


class CPCreateRequest(BaseModel):
    """Request to create a Check Point."""
    code: str = Field(..., min_length=1, description="CP code e.g. A3.1")
    name: str = Field(..., min_length=1)
    owner: str = Field(..., min_length=1)
    description: Optional[str] = None
    domain: Optional[TrackerDomain] = None
    stream: Optional[TrackerStream] = None
    uom: Optional[str] = None
    target_from: Optional[str] = None
    target_to: Optional[str] = None
    target_quarter: Optional[TargetQuarter] = None


class CPUpdateRequest(BaseModel):
    """Request to update a Check Point."""
    code: Optional[str] = Field(None, min_length=1)
    name: Optional[str] = Field(None, min_length=1)
    owner: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    domain: Optional[TrackerDomain] = None
    stream: Optional[TrackerStream] = None
    uom: Optional[str] = None
    target_from: Optional[str] = None
    target_to: Optional[str] = None
    target_quarter: Optional[TargetQuarter] = None


class ProjectCreateRequest(BaseModel):
    """Request to create a Project."""
    name: str = Field(..., min_length=1)
    project_type: Optional[ProjectType] = None
    vendor: Optional[str] = None
    product_owner: Optional[str] = None
    engg_poc: Optional[str] = Field(None, description="TVSM Engineering POC(s), comma-separated")
    lob: Optional[BusinessUnit] = None
    bu: Optional[BusinessUnit] = None
    domain: Optional[TrackerDomain] = None
    stream: Optional[TrackerStream] = None
    description: Optional[str] = None

    @field_validator("vendor")
    @classmethod
    def validate_vendor(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_VENDORS:
            raise ValueError(f"Vendor must be one of: {', '.join(VALID_VENDORS)}")
        return v

    @field_validator("product_owner")
    @classmethod
    def validate_product_owner(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PRODUCT_OWNERS:
            raise ValueError(f"Product Owner must be one of: {', '.join(VALID_PRODUCT_OWNERS)}")
        return v


class ProjectUpdateRequest(BaseModel):
    """Request to update a Project."""
    name: Optional[str] = Field(None, min_length=1)
    project_type: Optional[ProjectType] = None
    vendor: Optional[str] = None
    product_owner: Optional[str] = None
    engg_poc: Optional[str] = Field(None, description="TVSM Engineering POC(s), comma-separated")
    lob: Optional[BusinessUnit] = None
    bu: Optional[BusinessUnit] = None
    domain: Optional[TrackerDomain] = None
    stream: Optional[TrackerStream] = None
    description: Optional[str] = None
    revised_target_date: Optional[date] = None

    @field_validator("vendor")
    @classmethod
    def validate_vendor(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_VENDORS:
            raise ValueError(f"Vendor must be one of: {', '.join(VALID_VENDORS)}")
        return v

    @field_validator("product_owner")
    @classmethod
    def validate_product_owner(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PRODUCT_OWNERS:
            raise ValueError(f"Product Owner must be one of: {', '.join(VALID_PRODUCT_OWNERS)}")
        return v


class StageUpdateRequest(BaseModel):
    """Request to update a process track stage."""
    status: StageStatus
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    remarks: Optional[str] = None
    skip_reason: Optional[str] = None

    @model_validator(mode="after")
    def validate_status_fields(self):
        if self.status == StageStatus.COMPLETED and self.actual_date is None:
            raise ValueError("actual_date is required when marking a stage Completed")
        if self.status == StageStatus.SKIPPED and not self.skip_reason:
            raise ValueError("skip_reason is required when marking a stage Skipped")
        return self


class MilestoneCreateRequest(BaseModel):
    """Request to add a milestone to the execution track."""
    name: str = Field(..., min_length=1)
    vendor: Optional[str] = Field(default="")
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    remarks: Optional[str] = None

    @field_validator("vendor")
    @classmethod
    def validate_vendor(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "" and v not in VALID_VENDORS:
            raise ValueError(f"Vendor must be one of: {', '.join(VALID_VENDORS)}")
        return v

    @model_validator(mode="after")
    def validate_dates(self):
        if self.planned_start and self.planned_end and self.planned_end < self.planned_start:
            raise ValueError("planned_end must be >= planned_start")
        return self


class MilestoneUpdateRequest(BaseModel):
    """Request to update a milestone."""
    name: Optional[str] = Field(None, min_length=1)
    vendor: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    remarks: Optional[str] = None
    # 3W1H context - mandatory when actual_end > planned_end (delay detected)
    delay_what: Optional[str] = None
    delay_why: Optional[str] = None
    delay_who: Optional[str] = None
    delay_owner_team: Optional[str] = None
    delay_how: Optional[str] = None
    delay_eta: Optional[date] = None


class RAGUpdateRequest(BaseModel):
    """Request to update RAG status with 3W1H context."""
    status: RAGStatus
    what: Optional[str] = None
    why: Optional[str] = None
    who: Optional[str] = None
    owner_team: Optional[str] = None
    how: Optional[str] = None
    eta: Optional[date] = None

    @model_validator(mode="after")
    def validate_context_for_non_green(self):
        if self.status in (RAGStatus.YELLOW, RAGStatus.RED):
            missing = []
            if not self.what:
                missing.append("what")
            if not self.why:
                missing.append("why")
            if not self.who:
                missing.append("who")
            if not self.owner_team:
                missing.append("owner_team")
            if not self.how:
                missing.append("how")
            if not self.eta:
                missing.append("eta")
            if missing:
                raise ValueError(
                    f"3W1H fields required for {self.status.value}: {', '.join(missing)}"
                )
        return self


class RAGContextUpdateRequest(BaseModel):
    """Request to update RAG context without changing status."""
    what: Optional[str] = None
    why: Optional[str] = None
    who: Optional[str] = None
    owner_team: Optional[str] = None
    how: Optional[str] = None
    eta: Optional[date] = None


class DependencyCreateRequest(BaseModel):
    """Request to create a dependency."""
    description: str = Field(..., min_length=1)
    external_owner: str = Field(..., min_length=1)
    cutoff_date: date
    milestone_id: Optional[str] = None
    status: DependencyStatus = DependencyStatus.OPEN
    is_blocker: bool = False


class DependencyUpdateRequest(BaseModel):
    """Request to update a dependency."""
    description: Optional[str] = Field(None, min_length=1)
    external_owner: Optional[str] = Field(None, min_length=1)
    cutoff_date: Optional[date] = None
    milestone_id: Optional[str] = None
    status: Optional[DependencyStatus] = None
    escalation_note: Optional[str] = None
    is_blocker: Optional[bool] = None


class BudgetUpdateRequest(BaseModel):
    """Request to update budget metadata."""
    approved_budget: Optional[float] = None
    internal_estimate: Optional[float] = None
    quarterly_plan: Optional[Dict[str, float]] = Field(None, description="Planned budget per quarter: {Q1: x, Q2: x, Q3: x, Q4: x}")
    remarks: Optional[str] = None


class BudgetTransactionCreateRequest(BaseModel):
    """Request to add a budget transaction."""
    transaction_type: BudgetTransactionType
    po_number: Optional[str] = None
    vendor: Optional[str] = None
    amount: float = Field(..., gt=0)
    date: date
    quarter: Optional[str] = Field(None, description="Quarter tag: Q1, Q2, Q3, Q4")
    remarks: Optional[str] = None


# =============================================================================
# MILESTONE TASKS (Sub-tasks under milestones)
# =============================================================================


class MilestoneTask(BaseModel):
    """A task/story under a milestone in the execution track."""
    id: str = Field(...)
    milestone_id: str = Field(...)
    name: str = Field(...)
    owner: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    slippage_days: Optional[int] = None
    is_delayed: bool = False
    rag_status: RAGStatus = Field(default=RAGStatus.GREEN)
    rag_context: List[RAGContext] = Field(default_factory=list)
    remarks: Optional[str] = None


class MilestoneTaskCreateRequest(BaseModel):
    """Request to create a task under a milestone."""
    name: str = Field(..., min_length=1)
    owner: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    remarks: Optional[str] = None


class MilestoneTaskUpdateRequest(BaseModel):
    """Request to update a milestone task."""
    name: Optional[str] = None
    owner: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    remarks: Optional[str] = None
    # 3W1H context - mandatory when actual_end > planned_end (delay detected)
    delay_what: Optional[str] = None
    delay_why: Optional[str] = None
    delay_who: Optional[str] = None
    delay_owner_team: Optional[str] = None
    delay_how: Optional[str] = None
    delay_eta: Optional[date] = None


# =============================================================================
# RESPONSE MODELS
# =============================================================================


class MPResponse(ManagingPoint):
    """Response model for a Managing Point."""
    pass


class CPResponse(CheckPoint):
    """Response model for a Check Point."""
    pass


class ProjectResponse(Project):
    """Response model for a Project."""
    pass


class ProcessTrackResponse(BaseModel):
    """Full process track for a project."""
    project_id: str
    stages: List[ProcessTrackStage]
    current_stage: Optional[ProcessStage] = None


class ExecutionTrackResponse(BaseModel):
    """Full execution track for a project."""
    project_id: str
    milestones: List[ExecutionMilestone]
    total_planned_days: int = 0
    total_actual_days: int = 0
    cumulative_slippage: int = 0
    revised_target_date: Optional[date] = None
    fast_track_days: Optional[int] = None
    time_axis_start: Optional[date] = None
    time_axis_end: Optional[date] = None


class DashboardMetrics(BaseModel):
    """Aggregated dashboard metrics."""
    total_projects: int = 0
    green_count: int = 0
    yellow_count: int = 0
    red_count: int = 0
    open_dependencies: int = 0
    budget_total_approved: float = 0.0
    budget_total_exhausted: float = 0.0
    budget_total_remaining: float = 0.0
    budget_over_count: int = 0
    by_vendor: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    by_po: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_lob: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    by_domain_bu_stream: List[Dict[str, Any]] = Field(default_factory=list)
    critical_items: List[Dict[str, Any]] = Field(default_factory=list)
    open_dependencies_list: List[Dict[str, Any]] = Field(default_factory=list)


class BulkUploadResponse(BaseModel):
    """Response from bulk milestone upload."""
    success: bool
    milestones_added: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class WeeklyReportConfig(BaseModel):
    """Configuration for weekly email report."""
    to: List[str] = Field(default_factory=list)
    cc: List[str] = Field(default_factory=list)
    bu_filter: Optional[BusinessUnit] = None
    include_all_bus: bool = True
