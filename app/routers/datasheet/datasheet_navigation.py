from fastapi import APIRouter, HTTPException
from app.schemas.datasheet import (
    NavSourceRequest,
    NavPlanRequest,
    NavEndpointRequest,
    NavEndpointRequiredRequest,
    NavPlansResponse,
    NavEndpointsResponse,
    NavCapacityUnitsResponse,
    NavAliasesResponse,
    NavCRFRangesResponse,
    CRFRange,
)
from app.services.datasheet_evaluator_service import DatasheetEvaluatorService
from app.utils.yaml_utils import load_yaml_source

router = APIRouter()
evaluator_service = DatasheetEvaluatorService()


@router.post("/plans", response_model=NavPlansResponse,
             summary="List available billing plans in the datasheet")
def get_plans(request: NavSourceRequest):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        return NavPlansResponse(plans=evaluator_service.get_plans(yaml_data))
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/endpoints", response_model=NavEndpointsResponse,
             summary="List endpoints available in a given plan")
def get_endpoints(request: NavPlanRequest):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        return NavEndpointsResponse(
            plan=request.plan_name,
            endpoints=evaluator_service.get_endpoints(yaml_data, request.plan_name),
        )
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/capacity-units", response_model=NavCapacityUnitsResponse,
             response_model_exclude_none=True,
             summary="List workload-based capacity units. plan_name and endpoint_path are optional filters; omit both to get the union across the entire datasheet.")
def get_capacity_units(request: NavEndpointRequest):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        units = evaluator_service.get_capacity_units(
            yaml_data, request.plan_name, request.endpoint_path
        )
        return NavCapacityUnitsResponse(
            plan=request.plan_name,
            endpoint=request.endpoint_path,
            units=units,
        )
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/aliases", response_model=NavAliasesResponse,
             response_model_exclude_none=True,
             summary="List aliases for a specific endpoint (null if none)")
def get_aliases(request: NavEndpointRequiredRequest):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        aliases = evaluator_service.get_aliases(
            yaml_data, request.plan_name, request.endpoint_path
        )
        return NavAliasesResponse(
            plan=request.plan_name,
            endpoint=request.endpoint_path,
            aliases=aliases,
        )
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/crf-ranges", response_model=NavCRFRangesResponse,
             response_model_exclude_none=True,
             summary="Return the min/max CRF range per workload unit for an endpoint")
def get_crf_ranges(request: NavEndpointRequiredRequest):
    yaml_data = load_yaml_source(request.datasheet_source)
    try:
        raw = evaluator_service.get_crf_ranges(
            yaml_data, request.plan_name, request.endpoint_path
        )
        return NavCRFRangesResponse(
            plan=request.plan_name,
            endpoint=request.endpoint_path,
            crf_ranges=[CRFRange(**r) for r in raw],
        )
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))
