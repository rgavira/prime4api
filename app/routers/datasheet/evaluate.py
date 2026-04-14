from fastapi import APIRouter, HTTPException
from app.schemas.datasheet import EvaluateDatasheetRequest, EvaluateDatasheetResponse
from app.services.datasheet_evaluator_service import DatasheetEvaluatorService
from app.utils.yaml_utils import load_yaml_source

router = APIRouter()
evaluator_service = DatasheetEvaluatorService()


@router.post("/evaluate", response_model=EvaluateDatasheetResponse)
def evaluate_datasheet(request: EvaluateDatasheetRequest):
    yaml_data = load_yaml_source(request.datasheet_source)

    try:
        results = evaluator_service.evaluate(yaml_data, request)
        return EvaluateDatasheetResponse(
            operation=request.operation,
            operation_params=request.operation_params,
            results=results
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Key not found in Datasheet: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal evaluation error: {str(e)}")
