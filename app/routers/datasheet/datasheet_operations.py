from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models import Rate, Quota
from app.schemas.datasheet import (
    DatasheetBaseRequest,
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
from .evaluate import load_yaml_source

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


@router.post("/min-time", response_model=DatasheetMinTimeResponse)
def get_min_time(
    request: DatasheetBaseRequest,
    capacity_goal: int = Query(..., description="Capacity goal"),
):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        raw = evaluator_service.evaluate(yaml_data, _build_request(request, "min_time", {"capacity_goal": capacity_goal}))
        return DatasheetMinTimeResponse(
            capacity_goal=capacity_goal,
            results=[DatasheetMinTimeResultItem(endpoint=r.endpoint, alias=r.alias, min_time=r.result) for r in raw],
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capacity-at", response_model=DatasheetCapacityAtResponse)
def get_capacity_at(
    request: DatasheetBaseRequest,
    time: str = Query(..., description="Time instant (e.g. '1h', '1day')"),
):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        raw = evaluator_service.evaluate(yaml_data, _build_request(request, "capacity_at", {"time": time}))
        return DatasheetCapacityAtResponse(
            time=time,
            results=[DatasheetCapacityAtResultItem(endpoint=r.endpoint, alias=r.alias, capacity=r.result) for r in raw],
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
):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        raw = evaluator_service.evaluate(
            yaml_data,
            _build_request(request, "capacity_during", {"end_instant": end_instant, "start_instant": start_instant}),
        )
        return DatasheetCapacityDuringResponse(
            start_instant=start_instant,
            end_instant=end_instant,
            results=[DatasheetCapacityDuringResultItem(endpoint=r.endpoint, alias=r.alias, capacity=r.result) for r in raw],
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quota-exhaustion-threshold", response_model=DatasheetQuotaExhaustionResponse)
def get_quota_exhaustion_threshold(request: DatasheetBaseRequest):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        raw = evaluator_service.evaluate(yaml_data, _build_request(request, "quota_exhaustion_threshold", {}))
        return DatasheetQuotaExhaustionResponse(
            results=[
                DatasheetQuotaExhaustionResultItem(endpoint=r.endpoint, alias=r.alias, thresholds=r.result)
                for r in raw
            ]
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/idle-time-period", response_model=DatasheetIdleTimePeriodResponse)
def get_idle_time_period(request: DatasheetBaseRequest):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        raw = evaluator_service.evaluate(yaml_data, _build_request(request, "idle_time_period", {}))
        return DatasheetIdleTimePeriodResponse(
            results=[
                DatasheetIdleTimePeriodResultItem(endpoint=r.endpoint, alias=r.alias, idle_times=r.result)
                for r in raw
            ]
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
            results=[DatasheetRatesResultItem(endpoint=r.endpoint, alias=r.alias, rates=r.result) for r in raw]
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
            results=[DatasheetQuotasResultItem(endpoint=r.endpoint, alias=r.alias, quotas=r.result) for r in raw]
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
        results = []
        for r in raw:
            limits = r.result  # List[Rate | Quota]
            results.append(DatasheetLimitsResultItem(
                endpoint=r.endpoint,
                alias=r.alias,
                rates=[l for l in limits if isinstance(l, Rate)],
                quotas=[l for l in limits if isinstance(l, Quota)],
            ))
        return DatasheetLimitsResponse(results=results)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
