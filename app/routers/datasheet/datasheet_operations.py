from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models import Rate, Quota
from app.schemas.datasheet import (
    DatasheetBaseRequest,
    DimensionResult, CaseResult,
    DatasheetMinTimeResponse, DatasheetMinTimeResultItem,
    DatasheetCapacityAtResponse, DatasheetCapacityAtResultItem,
    DatasheetCapacityDuringResponse, DatasheetCapacityDuringResultItem,
    DatasheetQuotaExhaustionResponse, DatasheetQuotaExhaustionResultItem,
    DatasheetIdleTimePeriodResponse, DatasheetIdleTimePeriodResultItem,
    DatasheetRatesResponse, DatasheetRatesResultItem,
    DatasheetQuotasResponse, DatasheetQuotasResultItem,
    DatasheetLimitsResponse, DatasheetLimitsResultItem,
    EvaluateDatasheetRequest,
)
from app.services.datasheet_evaluator_service import DatasheetEvaluatorService
from app.utils.yaml_utils import load_yaml_source

router = APIRouter()
evaluator_service = DatasheetEvaluatorService()


def _build_request(base: DatasheetBaseRequest, operation: str, operation_params: dict) -> EvaluateDatasheetRequest:
    return EvaluateDatasheetRequest(
        datasheet_source=base.datasheet_source,
        plan_name=base.plan_name,
        endpoint_path=base.endpoint_path,
        alias=base.alias,
        operation=operation,
        operation_params=operation_params,
    )


def _group_dimensions(result) -> dict:
    """Groups a flat List[DimensionResult] into Dict[dimension, List[CaseResult]]."""
    if not isinstance(result, list) or not result or not isinstance(result[0], DimensionResult):
        return {"requests": [CaseResult(capacity_request_factor=None, value=result)]}
    grouped: dict = {}
    for dr in result:
        grouped.setdefault(dr.dimension, []).append(
            CaseResult(capacity_request_factor=dr.workload_factor, value=dr.value)
        )
    return grouped


def _crf_dict(capacity_unit: Optional[str], capacity_request_factor: Optional[int]) -> Optional[dict]:
    """Converts query params into the dict the service expects."""
    if capacity_unit and capacity_request_factor is not None:
        return {capacity_unit: capacity_request_factor}
    return None


@router.post("/min-time", response_model=DatasheetMinTimeResponse)
def get_min_time(
    request: DatasheetBaseRequest,
    capacity_goal: int = Query(..., description="Number of units to reach"),
    capacity_unit: Optional[str] = Query(None, description="Unit dimension to filter (e.g. 'emails', 'requests'). Returns all if omitted."),
    capacity_request_factor: Optional[int] = Query(None, description="Fixed workload value for capacity_unit (e.g. 500). Returns worst/avg/best range if omitted."),
):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        raw = evaluator_service.evaluate(
            yaml_data,
            _build_request(request, "min_time", {"capacity_goal": capacity_goal}),
            capacity_unit=capacity_unit,
            capacity_request_factor=_crf_dict(capacity_unit, capacity_request_factor),
        )
        return DatasheetMinTimeResponse(
            capacity_goal=capacity_goal,
            results={
                plan: [DatasheetMinTimeResultItem(endpoint=r.endpoint, alias=r.alias, dimensions=_group_dimensions(r.result)) for r in items]
                for plan, items in raw.items()
            },
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capacity-at", response_model=DatasheetCapacityAtResponse)
def get_capacity_at(
    request: DatasheetBaseRequest,
    time: str = Query(..., description="Time instant (e.g. '1h', '1day')"),
    capacity_unit: Optional[str] = Query(None, description="Unit dimension to filter (e.g. 'emails', 'requests'). Returns all if omitted."),
    capacity_request_factor: Optional[int] = Query(None, description="Fixed workload value for capacity_unit. Returns worst/avg/best range if omitted."),
):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        raw = evaluator_service.evaluate(
            yaml_data,
            _build_request(request, "capacity_at", {"time": time}),
            capacity_unit=capacity_unit,
            capacity_request_factor=_crf_dict(capacity_unit, capacity_request_factor),
        )
        return DatasheetCapacityAtResponse(
            time=time,
            results={
                plan: [DatasheetCapacityAtResultItem(endpoint=r.endpoint, alias=r.alias, dimensions=_group_dimensions(r.result)) for r in items]
                for plan, items in raw.items()
            },
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capacity-during", response_model=DatasheetCapacityDuringResponse)
def get_capacity_during(
    request: DatasheetBaseRequest,
    end_instant: str = Query(..., description="End time instant (e.g. '1day')"),
    start_instant: Optional[str] = Query("0ms", description="Start time instant (e.g. '0ms')"),
    capacity_unit: Optional[str] = Query(None, description="Unit dimension to filter (e.g. 'emails', 'requests'). Returns all if omitted."),
    capacity_request_factor: Optional[int] = Query(None, description="Fixed workload value for capacity_unit. Returns worst/avg/best range if omitted."),
):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        raw = evaluator_service.evaluate(
            yaml_data,
            _build_request(request, "capacity_during", {"end_instant": end_instant, "start_instant": start_instant}),
            capacity_unit=capacity_unit,
            capacity_request_factor=_crf_dict(capacity_unit, capacity_request_factor),
        )
        return DatasheetCapacityDuringResponse(
            start_instant=start_instant,
            end_instant=end_instant,
            results={
                plan: [DatasheetCapacityDuringResultItem(endpoint=r.endpoint, alias=r.alias, dimensions=_group_dimensions(r.result)) for r in items]
                for plan, items in raw.items()
            },
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quota-exhaustion-threshold", response_model=DatasheetQuotaExhaustionResponse)
def get_quota_exhaustion_threshold(
    request: DatasheetBaseRequest,
    capacity_unit: Optional[str] = Query(None, description="Unit dimension to filter (e.g. 'emails', 'requests'). Returns all if omitted."),
    capacity_request_factor: Optional[int] = Query(None, description="Fixed workload value for capacity_unit. Returns worst/avg/best range if omitted."),
):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        raw = evaluator_service.evaluate(
            yaml_data,
            _build_request(request, "quota_exhaustion_threshold", {}),
            capacity_unit=capacity_unit,
            capacity_request_factor=_crf_dict(capacity_unit, capacity_request_factor),
        )
        return DatasheetQuotaExhaustionResponse(
            results={
                plan: [DatasheetQuotaExhaustionResultItem(endpoint=r.endpoint, alias=r.alias, dimensions=_group_dimensions(r.result)) for r in items]
                for plan, items in raw.items()
            }
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/idle-time-period", response_model=DatasheetIdleTimePeriodResponse)
def get_idle_time_period(
    request: DatasheetBaseRequest,
    capacity_unit: Optional[str] = Query(None, description="Unit dimension to filter (e.g. 'emails', 'requests'). Returns all if omitted."),
    capacity_request_factor: Optional[int] = Query(None, description="Fixed workload value for capacity_unit. Returns worst/avg/best range if omitted."),
):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        raw = evaluator_service.evaluate(
            yaml_data,
            _build_request(request, "idle_time_period", {}),
            capacity_unit=capacity_unit,
            capacity_request_factor=_crf_dict(capacity_unit, capacity_request_factor),
        )
        return DatasheetIdleTimePeriodResponse(
            results={
                plan: [DatasheetIdleTimePeriodResultItem(endpoint=r.endpoint, alias=r.alias, dimensions=_group_dimensions(r.result)) for r in items]
                for plan, items in raw.items()
            }
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rates", response_model=DatasheetRatesResponse)
def get_rates(request: DatasheetBaseRequest):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        raw = evaluator_service.evaluate(yaml_data, _build_request(request, "rates", {}))
        return DatasheetRatesResponse(
            results={
                plan: [DatasheetRatesResultItem(endpoint=r.endpoint, alias=r.alias, rates=r.result) for r in items]
                for plan, items in raw.items()
            }
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quotas", response_model=DatasheetQuotasResponse)
def get_quotas(request: DatasheetBaseRequest):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        raw = evaluator_service.evaluate(yaml_data, _build_request(request, "quotas", {}))
        return DatasheetQuotasResponse(
            results={
                plan: [DatasheetQuotasResultItem(endpoint=r.endpoint, alias=r.alias, quotas=r.result) for r in items]
                for plan, items in raw.items()
            }
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/limits", response_model=DatasheetLimitsResponse)
def get_limits(request: DatasheetBaseRequest):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        raw = evaluator_service.evaluate(yaml_data, _build_request(request, "limits", {}))
        return DatasheetLimitsResponse(
            results={
                plan: [
                    DatasheetLimitsResultItem(
                        endpoint=r.endpoint,
                        alias=r.alias,
                        rates=[l for l in r.result if isinstance(l, Rate)],
                        quotas=[l for l in r.result if isinstance(l, Quota)],
                    )
                    for r in items
                ]
                for plan, items in raw.items()
            }
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
