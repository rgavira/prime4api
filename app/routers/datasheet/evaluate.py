from fastapi import APIRouter, HTTPException
import yaml
import requests
from app.schemas.datasheet import EvaluateDatasheetRequest, EvaluateDatasheetResponse
from app.services.datasheet_evaluator_service import DatasheetEvaluatorService

router = APIRouter()
evaluator_service = DatasheetEvaluatorService()

def load_yaml_source(source: str) -> dict:
    if source.startswith("http://") or source.startswith("https://"):
        try:
            response = requests.get(source)
            response.raise_for_status()
            yaml_content = response.text
        except requests.RequestException as e:
            raise HTTPException(status_code=400, detail=f"Error fetching Datasheet URI: {str(e)}")
    else:
        yaml_content = source

    try:
        return yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML format: {str(e)}")


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
