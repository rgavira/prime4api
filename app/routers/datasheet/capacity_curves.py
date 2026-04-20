from fastapi import APIRouter, HTTPException, Query, Response
from typing import Optional

from app.schemas.datasheet import DatasheetBaseRequest, DatasheetCurveSeries, DatasheetCurveDataResponse
from app.schemas.datasheet import EvaluateDatasheetRequest
from app.services.datasheet_evaluator_service import DatasheetEvaluatorService
from app.services.capacity_curve_service import CapacityCurveService
from app.utils.yaml_utils import load_yaml_source
from app.utils.plotly_renderer import render_multi_curve_html
from app.utils.time_utils import parse_time_string_to_duration, select_best_time_unit

router = APIRouter()
evaluator_service = DatasheetEvaluatorService()
curve_service = CapacityCurveService()

_CURVE_QUERY = dict(description="Time window for the curve (e.g. '1day', '1month')")
_UNIT_QUERY  = dict(description="Filter to a single dimension (e.g. 'emails', 'requests'). Returns all if omitted.")
_CRF_QUERY   = dict(description="Fixed workload value for capacity_unit. Returns worst/avg/best range if omitted.")


def _build_nav_request(base: DatasheetBaseRequest) -> EvaluateDatasheetRequest:
    return EvaluateDatasheetRequest(
        datasheet_source=base.datasheet_source,
        plan_name=base.plan_name,
        endpoint_path=base.endpoint_path,
        alias=base.alias,
        operation="__nav__",
        operation_params={},
    )


def _crf_dict(capacity_unit, capacity_request_factor):
    if capacity_unit and capacity_request_factor is not None:
        return {capacity_unit: capacity_request_factor}
    return None


def _time_axis_params(time_interval: str):
    td = parse_time_string_to_duration(time_interval)
    best = select_best_time_unit(td.to_milliseconds())
    return best.unit.value, best.unit.to_milliseconds()


def _series_label(sc: dict) -> str:
    crf = f" | CRF={sc['crf']}" if sc["crf"] is not None else ""
    alias = f" [{sc['alias']}]" if sc["alias"] != "default" else ""
    return f"{sc['plan']} / {sc['endpoint']}{alias} — {sc['dimension']}{crf}"


def _get_curve_points(sc: dict, time_interval: str, curve_type: str):
    rates  = sc["rates"]  if sc["rates"]  else None
    quotas = sc["quotas"] if sc["quotas"] else None
    if curve_type == "accumulated":
        return curve_service.get_accumulated_capacity_curve(time_interval, rates, quotas)
    return curve_service.get_inflection_point_capacity_curve(time_interval, rates, quotas)


def _render_chart(base, time_interval, capacity_unit, capacity_request_factor, curve_type, line_shape):
    data = _render_data(base, time_interval, capacity_unit, capacity_request_factor, curve_type)

    series_list = [
        {
            "plan":          s.plan,
            "endpoint":      s.endpoint,
            "alias":         s.alias,
            "dimension":     s.dimension,
            "workload_unit": s.workload_unit,
            "crf":           s.capacity_request_factor,
            "rates":         s.rates,
            "quotas":        s.quotas,
            "t_ms":          s.t_ms,
            "capacity":      s.capacity,
        }
        for s in data.series
    ]

    if not series_list:
        raise ValueError("No valid curves could be generated for the given parameters.")

    x_unit_label, x_scale_divisor = _time_axis_params(time_interval)
    title = f"{'Accumulated' if curve_type == 'accumulated' else 'Inflection Point'} Capacity Curve — {time_interval}"
    return render_multi_curve_html(series_list, title, line_shape, x_unit_label, x_scale_divisor)


def _render_data(base, time_interval, capacity_unit, capacity_request_factor, curve_type):
    yaml_data = load_yaml_source(base.datasheet_source)
    scenarios = evaluator_service.get_curve_scenarios(
        yaml_data,
        _build_nav_request(base),
        capacity_unit=capacity_unit,
        capacity_request_factor=_crf_dict(capacity_unit, capacity_request_factor),
    )

    series = []
    for sc in scenarios:
        try:
            pts = _get_curve_points(sc, time_interval, curve_type)
            series.append(DatasheetCurveSeries(
                plan=sc["plan"],
                endpoint=sc["endpoint"],
                alias=sc["alias"],
                dimension=sc["dimension"],
                workload_unit=sc.get("workload_unit"),
                capacity_request_factor=sc["crf"],
                rates=sc["rates"],
                quotas=sc["quotas"],
                t_ms=pts.t_ms,
                capacity=pts.capacity,
            ))
        except Exception as e:
            print(f"[WARNING] Skipping data for {_series_label(sc)}: {e}")

    return DatasheetCurveDataResponse(
        time_interval=time_interval,
        curve_type=curve_type,
        series=series,
    )


# ══════════════════════════════════════════════════════════════════════════════
# /data/*
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/data/accumulated", response_model=DatasheetCurveDataResponse,
             summary="Accumulated capacity curve — raw data points (datasheet)")
def get_accumulated_data(
    request: DatasheetBaseRequest,
    time_interval: str = Query(..., **_CURVE_QUERY),
    capacity_unit: Optional[str] = Query(None, **_UNIT_QUERY),
    capacity_request_factor: Optional[float] = Query(None, **_CRF_QUERY),
):
    try:
        return _render_data(request, time_interval, capacity_unit, capacity_request_factor, "accumulated")
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/inflection", response_model=DatasheetCurveDataResponse,
             summary="Inflection point capacity curve — raw data points (datasheet)")
def get_inflection_data(
    request: DatasheetBaseRequest,
    time_interval: str = Query(..., **_CURVE_QUERY),
    capacity_unit: Optional[str] = Query(None, **_UNIT_QUERY),
    capacity_request_factor: Optional[float] = Query(None, **_CRF_QUERY),
):
    try:
        return _render_data(request, time_interval, capacity_unit, capacity_request_factor, "inflection")
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# /chart/*
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/chart/accumulated",
    responses={200: {"content": {"text/html": {}}, "description": "Interactive Plotly chart (multi-curve)."}},
    summary="Accumulated capacity curve — interactive HTML chart (datasheet)",
)
def get_accumulated_chart(
    request: DatasheetBaseRequest,
    time_interval: str = Query(..., **_CURVE_QUERY),
    capacity_unit: Optional[str] = Query(None, **_UNIT_QUERY),
    capacity_request_factor: Optional[float] = Query(None, **_CRF_QUERY),
):
    try:
        html = _render_chart(request, time_interval, capacity_unit, capacity_request_factor, "accumulated", "hv")
        return Response(content=html, media_type="text/html")
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/chart/inflection",
    responses={200: {"content": {"text/html": {}}, "description": "Interactive Plotly chart (inflection, multi-curve)."}},
    summary="Inflection point capacity curve — interactive HTML chart (datasheet)",
)
def get_inflection_chart(
    request: DatasheetBaseRequest,
    time_interval: str = Query(..., **_CURVE_QUERY),
    capacity_unit: Optional[str] = Query(None, **_UNIT_QUERY),
    capacity_request_factor: Optional[float] = Query(None, **_CRF_QUERY),
):
    try:
        html = _render_chart(request, time_interval, capacity_unit, capacity_request_factor, "inflection", "linear")
        return Response(content=html, media_type="text/html")
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
