from dataclasses import dataclass, field
from typing import List


@dataclass
class CapacityCurvePoints:
    """
    Salida canónica de todos los plotters.

    t_ms      : valores del eje de tiempo en milisegundos (agnóstico de unidad).
    capacity  : capacidad acumulada disponible en cada instante t.

    Invariantes:
      - len(t_ms) == len(capacity) siempre.
      - t_ms[0] == 0.0 siempre.
      - t_ms[-1] == t_max (el extremo del intervalo solicitado) siempre.
      - t_ms está ordenado de menor a mayor.
    """
    t_ms: List[float] = field(default_factory=list)
    capacity: List[float] = field(default_factory=list)