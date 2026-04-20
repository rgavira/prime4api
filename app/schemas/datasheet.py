from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from app.models import Rate, Quota


# ──────────────────────────────────────────────────────────────────────────────
# Dimension result (one entry per unit-dimension × workload scenario)
# ──────────────────────────────────────────────────────────────────────────────

class DimensionResult(BaseModel):
    dimension: str
    workload_factor: Optional[float] = None  # actual emails/req used; None when no workload
    value: Any

class CaseResult(BaseModel):
    capacity_request_factor: Optional[float] = None
    value: Any


# ──────────────────────────────────────────────────────────────────────────────
# Base / evaluate (agente MCP)
# ──────────────────────────────────────────────────────────────────────────────

class EvaluateDatasheetRequest(BaseModel):
    datasheet_source: str = Field(..., description="The raw YAML text OR a valid URI to download the file.")
    plan_name: Optional[str] = Field(None, description="The target billing plan (e.g., 'free', 'pro'). If omitted, evaluates ALL plans.")
    endpoint_path: Optional[str] = Field(None, description="The specific endpoint. If omitted, will evaluate ALL endpoints.")
    alias: Optional[str] = Field(None, description="Filter by alias. If omitted, evaluates ALL existing aliases.")
    operation: str = Field(..., description="The calculation to perform: 'min_time', 'capacity_at', 'idle_time', etc.")
    operation_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Dynamic parameters for the operation (e.g., {'capacity_goal': 28}).")


class EvaluateDatasheetResultItem(BaseModel):
    endpoint: str
    alias: str
    result: Any


class EvaluateDatasheetResponse(BaseModel):
    operation: str
    operation_params: Dict[str, Any]
    results: Dict[str, List[EvaluateDatasheetResultItem]]


# ──────────────────────────────────────────────────────────────────────────────
# Base request para endpoints user-friendly
# ──────────────────────────────────────────────────────────────────────────────

class DatasheetBaseRequest(BaseModel):
    datasheet_source: str = Field(..., description="Raw YAML text OR a valid URI to download the datasheet.")
    plan_name: Optional[str] = Field(None, description="The target billing plan (e.g., 'free', 'pro'). If omitted, evaluates ALL plans.")
    endpoint_path: Optional[str] = Field(None, description="Filter by endpoint. If omitted, evaluates ALL endpoints.")
    alias: Optional[str] = Field(None, description="Filter by alias. If omitted, evaluates ALL aliases.")


# ──────────────────────────────────────────────────────────────────────────────
# Result items for calculation operations (return dimensions)
# ──────────────────────────────────────────────────────────────────────────────

class DatasheetMinTimeResultItem(BaseModel):
    endpoint: str
    alias: str
    dimensions: Dict[str, List[CaseResult]]

class DatasheetCapacityAtResultItem(BaseModel):
    endpoint: str
    alias: str
    dimensions: Dict[str, List[CaseResult]]

class DatasheetCapacityDuringResultItem(BaseModel):
    endpoint: str
    alias: str
    dimensions: Dict[str, List[CaseResult]]

class DatasheetQuotaExhaustionResultItem(BaseModel):
    endpoint: str
    alias: str
    dimensions: Dict[str, List[CaseResult]]

class DatasheetIdleTimePeriodResultItem(BaseModel):
    endpoint: str
    alias: str
    dimensions: Dict[str, List[CaseResult]]

class DatasheetRatesResultItem(BaseModel):
    endpoint: str
    alias: str
    rates: List[Rate]

class DatasheetQuotasResultItem(BaseModel):
    endpoint: str
    alias: str
    quotas: List[Quota]

class DatasheetLimitsResultItem(BaseModel):
    endpoint: str
    alias: str
    rates: List[Rate]
    quotas: List[Quota]


# ──────────────────────────────────────────────────────────────────────────────
# Responses por operación
# ──────────────────────────────────────────────────────────────────────────────

class DatasheetMinTimeResponse(BaseModel):
    capacity_goal: int
    results: Dict[str, List[DatasheetMinTimeResultItem]]

class DatasheetCapacityAtResponse(BaseModel):
    time: str
    results: Dict[str, List[DatasheetCapacityAtResultItem]]

class DatasheetCapacityDuringResponse(BaseModel):
    start_instant: str
    end_instant: str
    results: Dict[str, List[DatasheetCapacityDuringResultItem]]

class DatasheetQuotaExhaustionResponse(BaseModel):
    results: Dict[str, List[DatasheetQuotaExhaustionResultItem]]

class DatasheetIdleTimePeriodResponse(BaseModel):
    results: Dict[str, List[DatasheetIdleTimePeriodResultItem]]

class DatasheetRatesResponse(BaseModel):
    results: Dict[str, List[DatasheetRatesResultItem]]

class DatasheetQuotasResponse(BaseModel):
    results: Dict[str, List[DatasheetQuotasResultItem]]

class DatasheetLimitsResponse(BaseModel):
    results: Dict[str, List[DatasheetLimitsResultItem]]


# ──────────────────────────────────────────────────────────────────────────────
# Capacity curves
# ──────────────────────────────────────────────────────────────────────────────

class DatasheetCurveSeries(BaseModel):
    plan: str
    endpoint: str
    alias: str
    dimension: str
    workload_unit: Optional[str] = None
    capacity_request_factor: Optional[float] = None
    rates: List[Rate] = Field(default_factory=list)
    quotas: List[Quota] = Field(default_factory=list)
    t_ms: List[float]
    capacity: List[float]

class DatasheetCurveDataResponse(BaseModel):
    time_interval: str
    curve_type: str   # "accumulated" | "inflection"
    series: List[DatasheetCurveSeries]
