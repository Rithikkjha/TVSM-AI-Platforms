"""Pydantic models and shared types for the Project Estimation Tool."""

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


# --- Domain Types ---


class Domain(str, Enum):
    """Business domain classification."""

    SHOP = "Shop"
    BUY = "Buy"
    OWN = "Own"
    OTHERS = "Others"


class Stream(str, Enum):
    """Business stream / delivery channel classification."""

    CHANNEL_PARTNER = "Channel Partner"
    D2C = "D2C"
    PLATFORM_SERVICES = "Platform Services"


class Discipline(str, Enum):
    """Fixed set of allowed discipline names."""

    DIGITAL_ENGINEERING = "Digital Engineering"
    DATA_ENGINEERING = "Data Engineering"
    DATA_SCIENCE = "Data Science"
    DEVOPS = "DevOps"
    QA_TESTING = "QA/Testing"
    TECH_COE = "Tech COE"
    PRODUCT_DESIGN = "Product/Design"


class UserRole(str, Enum):
    """User authorization role."""

    ADMIN = "Admin"
    USER = "User"


InputTier = Literal[0, 1, 2, 3]

ScopeItemStatus = Literal["fully_estimated", "partially_estimated", "not_estimable"]

AuditEventType = Literal["generation", "revision"]


# --- Core Data Models ---


class DisciplineEffort(BaseModel):
    """Per-discipline effort breakdown."""

    discipline: str
    personDays: float = Field(..., gt=0, description="Effort in person-days")
    personMonths: float = Field(..., gt=0, description="Effort in person-months")


class TeamMember(BaseModel):
    """Recommended team member allocation per discipline."""

    discipline: str
    count: int = Field(..., gt=0)


class ScopeItem(BaseModel):
    """A discrete deliverable identified in the PRD."""

    id: str
    name: str
    type: Literal["feature", "user_story", "integration", "screen", "api_endpoint"]


class ClassifiedScopeItem(ScopeItem):
    """A scope item with estimation status classification."""

    status: ScopeItemStatus
    reason: Optional[str] = None


class TemplateComparison(BaseModel):
    """Result of comparing PRD scope against a base template."""

    matchedItems: list[str] = Field(
        default_factory=list, description="Template areas matched by PRD items"
    )
    unmatchedTemplateAreas: list[str] = Field(
        default_factory=list,
        description="Template areas not covered in PRD",
    )
    additionalPrdScope: list[str] = Field(
        default_factory=list,
        description="PRD items beyond template scope",
    )


class ScopeAnalysis(BaseModel):
    """Full scope coverage analysis."""

    items: list[ClassifiedScopeItem]
    coverage: float = Field(..., ge=0, le=1, description="Coverage ratio 0-1")
    recommendations: list[str] = []
    templateComparison: Optional[TemplateComparison] = None


class ConfidenceFactor(BaseModel):
    """Individual confidence factor with score and weight."""

    score: float = Field(..., ge=0, le=100)
    weight: float


class CompositeConfidenceScore(BaseModel):
    """Weighted composite confidence score from 5 factors."""

    overall: float = Field(..., ge=0, le=100)
    factors: dict[str, ConfidenceFactor] = Field(
        ...,
        description=(
            "Keys: inputCompleteness, documentDetail, requirementClarity, "
            "domainHistory, scopeCoverage"
        ),
    )
    recommendations: list[str] = []
    explanation: str = ""


class ConfidenceFactors(BaseModel):
    """Input factors for confidence calculation."""

    inputTier: InputTier
    documentDetailScore: float = Field(..., ge=0, le=100)
    requirementClarityScore: float = Field(..., ge=0, le=100)
    domainHistoryScore: float = Field(..., ge=0, le=100)
    scopeCoverageScore: float = Field(..., ge=0, le=100)


class RateCard(BaseModel):
    """Rate card configuration for cost calculations."""

    ratePerPersonMonth: float = Field(..., gt=0)
    workingDaysPerMonth: int = Field(default=22, gt=0)
    perDisciplineRates: dict[str, float] = Field(
        default_factory=dict,
        description="Per-discipline monthly rates. Falls back to ratePerPersonMonth if discipline not found."
    )


class CostProjection(BaseModel):
    """Cost projection derived from effort and rate card."""

    total: float = Field(..., ge=0)
    perDiscipline: list[dict] = Field(
        default_factory=list,
        description="List of {discipline, cost} dicts",
    )
    rateApplied: float = Field(..., gt=0)


class PhaseEstimation(BaseModel):
    """Per-phase effort estimation breakdown."""

    phaseName: str = Field(..., min_length=1, description="Phase name as detected from document")
    effortBreakdown: list[DisciplineEffort]
    totalPersonDays: float = Field(..., gt=0)
    totalPersonMonths: float = Field(..., gt=0)
    teamComposition: list[TeamMember] = Field(default_factory=list)
    calendarDuration: Optional[float] = Field(None, gt=0, description="Calendar months for this phase")
    costProjection: Optional[CostProjection] = None
    assumptions: list[str] = Field(default_factory=list)


class DurationResult(BaseModel):
    """Result of timeline/duration calculation."""

    totalCalendarMonths: float = Field(..., gt=0)
    perDiscipline: list[dict] = Field(
        default_factory=list,
        description="List of {discipline, calendarMonths} dicts",
    )
    rationale: str = ""


class ScenarioResult(BaseModel):
    """Result of a team scenario modeling run."""

    teamVariant: list[TeamMember]
    duration: DurationResult


# --- Document Models ---


class ValidationResult(BaseModel):
    """Result of document validation."""

    valid: bool
    error: Optional[str] = None


class ExtractedDocument(BaseModel):
    """A document that has been parsed and text-extracted."""

    filename: str
    format: Literal["pdf", "docx", "md"]
    pageCount: int = Field(..., ge=1)
    textContent: str
    readinessText: Optional[str] = None  # Markdown-formatted text for readiness assessment


class DocumentSet(BaseModel):
    """Set of input documents for estimation."""

    brd: ExtractedDocument
    prd: ExtractedDocument
    hld: Optional[ExtractedDocument] = None
    dependentServiceDocs: Optional[list[ExtractedDocument]] = None
    referenceSizing: Optional[str] = Field(None, description="Markdown table of team's reference t-shirt sizing from uploaded Excel")


# --- SLM Engine Models ---


class SLMConfig(BaseModel):
    """Configuration for the embedded SLM engine."""

    modelPath: str = Field(..., description="Path to GGUF model file")
    modelName: str = Field(..., description="e.g., 'qwen3-4b', 'gemma4-4b'")
    contextWindow: int = Field(..., gt=0, description="e.g., 4096, 8192")
    gpuLayers: Optional[int] = Field(
        default=None, description="Number of layers to offload to GPU (0 = CPU only)"
    )


class SLMOptions(BaseModel):
    """Options for a single SLM inference call."""

    temperature: Optional[float] = None
    maxTokens: Optional[int] = None
    topP: Optional[float] = None
    stopSequences: Optional[list[str]] = None


class SLMResponse(BaseModel):
    """Response from SLM inference."""

    content: str
    model: str
    usage: dict = Field(..., description="promptTokens, completionTokens")
    inferenceTimeMs: float


class SLMModelInfo(BaseModel):
    """Information about the currently loaded SLM model."""

    modelName: str
    modelPath: str
    parameterCount: str = Field(..., description="e.g., '4B'")
    contextWindow: int
    loaded: bool
    memoryUsageMB: float


# --- Request / Response Models ---


class EstimationRequest(BaseModel):
    """Request to generate a new estimation."""

    projectName: str = Field(..., min_length=1, description="Project name (mandatory)")
    projectDescription: Optional[str] = None
    domain: Domain
    stream: Stream
    documents: DocumentSet
    userId: str


class EstimationResult(BaseModel):
    """Complete estimation output."""

    id: str
    projectName: str
    projectDescription: Optional[str] = None
    domain: Domain
    stream: Stream
    inputTier: InputTier
    effortBreakdown: list[DisciplineEffort]
    totalEffortPersonDays: float = Field(..., gt=0)
    totalEffortPersonMonths: float = Field(..., gt=0)
    calendarDuration: float = Field(..., gt=0, description="Calendar months")
    teamComposition: list[TeamMember]
    scopeCoverage: ScopeAnalysis
    compositeConfidence: CompositeConfidenceScore
    costProjection: CostProjection
    infraCost: Optional[dict] = Field(default=None, description="Monthly cloud/infra cost breakdown")
    documentReadiness: Optional[dict] = Field(default=None, description="BRD/PRD readiness scores against templates")
    phases: Optional[list[PhaseEstimation]] = Field(
        default=None,
        description="Per-phase estimation breakdown. Null if document is not phased.",
    )
    catalogBreakdown: Optional["CatalogBreakdown"] = Field(
        default=None,
        description="Detailed catalog-based work item decomposition. Null if legacy engine used.",
    )
    assumptions: list[str] = Field(..., min_length=1)
    slmModelName: str = Field(..., min_length=1)
    timestamp: str


class ReEstimationResult(BaseModel):
    """Result of re-estimating an existing project."""

    currentEstimation: EstimationResult
    previousEstimation: EstimationResult
    changes: dict = Field(
        ..., description="Summary of differences between previous and current"
    )


# --- Catalog-Based Estimation Models ---


class CatalogWorkItem(BaseModel):
    """A single atomic work unit classified by the SLM from the catalog."""

    unitId: str = Field(..., description="Work unit ID from catalog (e.g., BE-05, FE-03)")
    complexity: str = Field(..., pattern="^(simple|medium|complex)$", description="Complexity tier")
    quantity: int = Field(..., ge=1, description="Number of instances of this work unit")
    system: str = Field(..., description="Target system from registry (e.g., DMS, TruChamp)")
    reason: str = Field(..., min_length=1, description="1-line explanation of why this unit was chosen")
    calculatedEffort: Optional[float] = Field(default=None, description="Effort in person-days (filled by calculator)")


class CatalogOverheadFlags(BaseModel):
    """Overhead context flags inferred by the SLM from PRD content."""

    teamSize: int = Field(default=3, ge=1, le=50, description="Expected team size")
    crossDomain: bool = Field(default=False, description="Whether D2C and CP systems are both involved")
    crossDomainSystems: list[str] = Field(default_factory=list, description="Systems crossing domains")
    techFamiliarityRisk: str = Field(default="proficient", pattern="^(proficient|learning|unfamiliar)$")
    dataVolumeEstimate: str = Field(default="<1K", description="Expected data volume band")
    multiRegion: bool = Field(default=False, description="Multi-region deployment needed")
    regionCount: int = Field(default=0, ge=0, description="Number of deployment regions")
    securityCritical: bool = Field(default=False, description="Involves PII or payment data")
    legacyTechDebt: bool = Field(default=False, description="Touches legacy/undocumented systems")


class CatalogClassificationResult(BaseModel):
    """Complete classification output from the SLM (no effort numbers — only categories)."""

    requirementTitle: str = Field(..., description="Short title inferred from PRD")
    targetSystems: list[str] = Field(..., min_length=1, description="Systems touched by this requirement")
    scopeType: str = Field(..., description="New Feature | Enhancement | Bug Fix | Migration | Integration")
    workItems: list[CatalogWorkItem] = Field(..., min_length=1, description="Decomposed atomic work units")
    integrationPatterns: list[str] = Field(default_factory=list, description="Integration patterns identified")
    overheadFlags: CatalogOverheadFlags = Field(default_factory=CatalogOverheadFlags)
    assumptions: list[str] = Field(default_factory=list, description="Assumptions made during classification")
    risks: list[str] = Field(default_factory=list, description="Risks identified from PRD gaps")


class CatalogCalculationResult(BaseModel):
    """Deterministic calculation result from the catalog calculator."""

    pointEstimate: float = Field(..., gt=0, description="Final effort estimate in person-days")
    confidenceLevel: str = Field(..., pattern="^(HIGH|MEDIUM|LOW)$")
    rangeLow: float = Field(..., gt=0, description="Lower bound of confidence range")
    rangeHigh: float = Field(..., gt=0, description="Upper bound of confidence range")
    baseEffort: float = Field(..., ge=0, description="Sum of unit efforts × quantities × multipliers")
    patternSurcharge: float = Field(default=0, ge=0, description="Integration pattern cost add-on")
    hubSurcharge: float = Field(default=0, ge=0, description="Hub system coordination cost add-on")
    overheadMultiplier: float = Field(default=1.0, ge=0.5, description="Compound overhead factor")
    aiMultiplier: float = Field(default=1.0, ge=0.5, le=1.0, description="AI productivity multiplier applied")
    workItems: list[CatalogWorkItem] = Field(..., description="Work items with calculatedEffort filled")
    disciplineBreakdown: list[DisciplineEffort] = Field(..., description="Effort mapped to disciplines")
    sanityWarnings: list[str] = Field(default_factory=list, description="Post-calculation warning flags")
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class CatalogBreakdown(BaseModel):
    """Detailed catalog-level breakdown for UI display in estimation results."""

    workItems: list[CatalogWorkItem] = Field(..., description="All classified work items with effort")
    overheadDetail: dict[str, float] = Field(default_factory=dict, description="Applied overhead factors")
    integrationPatterns: list[str] = Field(default_factory=list)
    hubSurcharges: dict[str, float] = Field(default_factory=dict, description="Hub → surcharge days applied")
    aiMultiplierApplied: float = Field(default=1.0)
    sanityWarnings: list[str] = Field(default_factory=list)
    confidenceLevel: str = Field(default="MEDIUM")
    rangeLow: float = Field(default=0)
    rangeHigh: float = Field(default=0)
    graphAugmentation: Optional[dict] = Field(default=None, description="Graph augmentation details: addedSystems, addedWorkItems, crossDomain info")


# --- Vendor Models ---


class VendorProposalInput(BaseModel):
    """Input for vendor bid comparison."""

    document: ExtractedDocument
    quotedCost: float = Field(..., gt=0)
    quotedTimeline: float = Field(..., gt=0, description="Months")
    vendorTeamSize: Optional[int] = None


class VendorQualityAssessment(BaseModel):
    """Quality assessment portion of vendor comparison."""

    scopeCoverage: float = Field(..., ge=0, le=1)
    gaps: list[str] = []
    addressed: list[str] = []


class VendorCostComparison(BaseModel):
    """Cost comparison portion of vendor analysis."""

    vendorCost: float
    internalCost: float
    variancePercent: float
    flagged: bool = Field(..., description="True if variance > 25%")


class VendorDeliveryComparison(BaseModel):
    """Delivery comparison portion of vendor analysis."""

    vendorTimeline: float
    internalTimeline: float
    teamSizeComparison: str
    flagged: bool


class VendorComparison(BaseModel):
    """Result of comparing a vendor proposal against internal estimation."""

    vendorName: str
    qualityAssessment: VendorQualityAssessment
    costComparison: VendorCostComparison
    deliveryComparison: VendorDeliveryComparison
    assumptions: list[str] = []
    overallRank: Optional[int] = None


class ConsolidatedVendorView(BaseModel):
    """Consolidated view of multiple vendor comparisons."""

    comparisons: list[VendorComparison]
    rankings: list[dict] = Field(
        default_factory=list,
        description="Vendors ranked by proximity to internal estimate",
    )


# --- Template Models ---


class BaseTemplate(BaseModel):
    """A base template associated with a Domain + Stream combination."""

    templateId: str
    domain: Domain
    stream: Stream
    scopeAreas: list[str] = Field(
        ..., description="Expected scope areas for this domain/stream"
    )
    defaultWeightings: Optional[dict] = None
    createdBy: str
    createdAt: str
    updatedAt: Optional[str] = None


# --- Audit Models ---


class AuditGenerationEntry(BaseModel):
    """Audit log entry for a new estimation generation event."""

    userId: str
    projectName: str
    domain: Domain
    stream: Stream
    inputTier: InputTier
    estimationValues: dict = Field(
        ..., description="Summary of generated estimation values"
    )
    slmModelName: str
    timestamp: str


class AuditRevisionEntry(BaseModel):
    """Audit log entry for a re-estimation / revision event."""

    userId: str
    projectName: str
    domain: Domain
    stream: Stream
    inputTier: InputTier
    previousValues: dict
    newValues: dict
    slmModelName: str
    timestamp: str
    estimationId: str


class AuditEntry(BaseModel):
    """Generic audit log entry (for query results)."""

    auditId: str
    eventType: AuditEventType
    userId: str
    projectName: str
    domain: Domain
    stream: Stream
    inputTier: InputTier
    previousValues: Optional[dict] = None
    newValues: Optional[dict] = None
    slmModelName: str
    timestamp: str
    estimationId: str


# --- User / Auth Models ---


class UserIdentity(BaseModel):
    """Authenticated user identity from SSO."""

    corporateId: str
    email: str
    displayName: str


class AllowlistEntry(BaseModel):
    """An entry in the user allowlist (Users.xlsx)."""

    corporateId: str
    email: str
    displayName: str
    role: UserRole
    addedBy: str
    addedAt: str
    active: bool = True


# --- Dashboard / Index Models ---


class EstimationIndexEntry(BaseModel):
    """Lightweight index entry for dashboard queries."""

    estimationId: str
    projectName: str
    domain: str = "Others"
    stream: str = "D2C"
    inputTier: int = 1
    confidenceScore: float = Field(default=0, ge=0, le=100)
    totalEffortDays: float = Field(default=0, ge=0)
    totalCost: float = Field(default=0, ge=0)
    scopeCoverage: float = Field(default=0, ge=0, le=1)
    generatedBy: str = ""
    generatedAt: str = ""
    monthlyFileRef: str = ""
    version: int = Field(default=1, ge=1)
    documentNames: list[str] = Field(default_factory=list, description="Filenames of uploaded documents")


class DashboardFilters(BaseModel):
    """Filters for the estimation history dashboard."""

    projectName: Optional[str] = None
    domain: Optional[Domain] = None
    stream: Optional[Stream] = None
    dateFrom: Optional[str] = None
    dateTo: Optional[str] = None


# --- Build vs Buy Enums ---


class OptionType(str, Enum):
    """Option type for Build vs Buy evaluation."""

    DO_NOTHING = "Do_Nothing"
    BUILD = "Build"
    BUY = "Buy"
    EXTEND = "Extend"


class EvaluationStatus(str, Enum):
    """Lifecycle status of a Build vs Buy evaluation."""

    DRAFT = "Draft"
    IN_PROGRESS = "In_Progress"
    SCORING_COMPLETE = "Scoring_Complete"
    RECOMMENDED = "Recommended"
    ARCHIVED = "Archived"


# --- Build vs Buy Request Models ---


class EvaluationCreateRequest(BaseModel):
    """Request to create a new Build vs Buy evaluation."""

    opportunity_name: str = Field(..., min_length=1)
    problem_statement: str = Field(..., min_length=1)
    business_unit: str = Field(..., min_length=1)
    budget_min: float = Field(..., ge=0)
    budget_max: float = Field(..., ge=0)
    target_decision_date: str


class OptionCreateRequest(BaseModel):
    """Request to add an option to an evaluation."""

    name: str = Field(..., min_length=1)
    type: OptionType
    vendor_name: Optional[str] = None
    description: Optional[str] = None


class OptionUpdateRequest(BaseModel):
    """Request to update an existing option."""

    name: Optional[str] = None
    vendor_name: Optional[str] = None
    description: Optional[str] = None


class ScoreSubmitRequest(BaseModel):
    """Request to submit dimension scores for an option."""

    scores: dict[str, int]  # dimension_key -> score (1-5)


class Year0CostsInput(BaseModel):
    """Year 0 (initial) cost breakdown input."""

    license: float = Field(default=0, ge=0)
    implementation: float = Field(default=0, ge=0)
    migration: float = Field(default=0, ge=0)
    infrastructure: float = Field(default=0, ge=0)
    training: float = Field(default=0, ge=0)
    professional_services: float = Field(default=0, ge=0)


class RecurringCostsInput(BaseModel):
    """Annual recurring costs input (Year 1-5)."""

    license_renewal: float = Field(default=0, ge=0)
    cloud: float = Field(default=0, ge=0)
    infrastructure: float = Field(default=0, ge=0)
    storage: float = Field(default=0, ge=0)
    ktlo_people: float = Field(default=0, ge=0)
    vendor_amc: float = Field(default=0, ge=0)
    change_requests: float = Field(default=0, ge=0)
    upgrades: float = Field(default=0, ge=0)
    support: float = Field(default=0, ge=0)


class TCOSubmitRequest(BaseModel):
    """Request to submit TCO data for an option."""

    year_0: Year0CostsInput
    yearly_costs: Optional[list[RecurringCostsInput]] = None
    user_count: Optional[int] = Field(None, gt=0)


class StatusUpdateRequest(BaseModel):
    """Request to update evaluation lifecycle status."""

    status: EvaluationStatus


# --- Build vs Buy Response Models ---


class BvBEvaluationResponse(BaseModel):
    """Response for a single Build vs Buy evaluation."""

    id: str
    opportunity_name: str
    problem_statement: str
    business_unit: str
    budget_min: float
    budget_max: float
    target_decision_date: str
    owner_display_name: str
    status: EvaluationStatus
    created_at: str
    updated_at: str


class BvBEvaluationListResponse(BaseModel):
    """Response for listing Build vs Buy evaluations."""

    evaluations: list[BvBEvaluationResponse]
    total: int


class OptionResponse(BaseModel):
    """Response for a single evaluation option."""

    id: str
    evaluation_id: str
    name: str
    type: OptionType
    vendor_name: Optional[str] = None
    description: Optional[str] = None


class DimensionScoreResponse(BaseModel):
    """Response for a single dimension score."""

    dimension: str
    score: int
    source: str
    confidence: Optional[float] = None


class ScoreResponse(BaseModel):
    """Response for option scoring results."""

    option_id: str
    scores: list[DimensionScoreResponse]
    weighted_total: float
    is_complete: bool
    unscored_dimensions: list[str]


class TCOResultResponse(BaseModel):
    """Response for TCO calculation results."""

    option_id: str
    year_0_total: float
    three_year_tco: float
    five_year_tco: float
    annual_run_cost: float
    cost_per_user: Optional[float] = None


class RecommendationResponse(BaseModel):
    """Response for evaluation recommendation."""

    ranked_options: list[dict]
    top_option_id: str
    top_option_name: str
    top_weighted_total: float


class ProposalAnalysisResponse(BaseModel):
    """Response for SLM vendor proposal analysis."""

    extracted_data: dict
    suggested_scores: dict[str, int]
    risk_flags: list[str]
    confidence: float
    error: Optional[str] = None


class ReportResponse(BaseModel):
    """Response for report generation."""

    report_filename: str
    generated_at: str


class BvBEvaluationDetailResponse(BaseModel):
    """Detailed response for a complete Build vs Buy evaluation."""

    evaluation: BvBEvaluationResponse
    options: list[OptionResponse]
    scores: dict[str, list[DimensionScoreResponse]]  # option_id -> scores
    tco_results: dict[str, TCOResultResponse]  # option_id -> TCO
    recommendation: Optional[RecommendationResponse] = None
