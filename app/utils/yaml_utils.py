import yaml
import requests
from fastapi import HTTPException


def _sanitize_yaml(text: str) -> str:
    """Elimina caracteres de control C1 (U+0080–U+009F) que YAML no permite
    y que suelen aparecer al copiar desde Word, PDF o editores Windows-1252."""
    return "".join(c for c in text if not ('\x80' <= c <= '\x9f'))


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
        return yaml.safe_load(_sanitize_yaml(yaml_content))
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML format: {str(e)}")
