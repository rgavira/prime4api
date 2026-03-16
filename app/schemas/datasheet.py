from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class EvaluateDatasheetRequest(BaseModel):
    datasheet_source: str = Field(..., description="The raw YAML text OR a valid URI to download the file.")
    plan_name: str = Field(..., description="The target billing plan (e.g., 'free', 'pro').")
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
    results: List[EvaluateDatasheetResultItem]
