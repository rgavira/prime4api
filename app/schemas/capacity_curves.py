from typing import List
from pydantic import BaseModel, Field
from app.schemas.basic_operations import BoundedRateRequest


# ── REQUEST ──────────────────────────────────────────────────────────────────

class CapacityCurveRequest(BoundedRateRequest):
    """
    Extiende BoundedRateRequest (que ya tiene rate y quota opcionales)
    añadiendo el intervalo de tiempo para la curva.
    """
    time_interval: str = Field(
        ...,
        description="Intervalo de tiempo para la curva, e.g. '1day', '2h', '30min'.",
        examples=["1day", "2h", "30min", "1month"],
    )


# ── RAW DATA RESPONSE ─────────────────────────────────────────────────────────

class CapacityCurvePointsResponse(BaseModel):
    """
    Respuesta de los endpoints /data/*.
    Contiene los puntos en bruto para que el cliente los plotee.
    t_ms está en milisegundos; el cliente elige la unidad de visualización.
    """
    t_ms: List[float] = Field(..., description="Valores del eje de tiempo en milisegundos.")
    capacity: List[float] = Field(..., description="Capacidad acumulada en cada instante t.")
    point_count: int = Field(..., description="Número de puntos en la curva.")
    time_interval: str = Field(..., description="Intervalo de tiempo solicitado.")
    curve_type: str = Field(
        ...,
        description="Tipo de curva: 'accumulated' | 'inflection' | 'normalized_inflection'.",
    )