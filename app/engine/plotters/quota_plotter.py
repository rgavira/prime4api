from typing import Union

from app.engine import TimeDuration, TimeUnit
from app.engine.evaluators import QuotaEvaluator
from app.engine.plotters.curve_models import CapacityCurvePoints
from app.models import Quota
from app.utils.time_utils import parse_time_string_to_duration


class QuotaPlotter:

    def __init__(self, quota: Quota):
        self.quota = quota
        self.evaluator = QuotaEvaluator(quota)

    def accumulated_capacity_curve(self, time_interval: Union[str, TimeDuration]) -> CapacityCurvePoints:

        if isinstance(time_interval, str):
            time_interval = parse_time_string_to_duration(time_interval)
        
        t_max_ms = int(time_interval.to_milliseconds())
        step = int(self.quota.period.to_milliseconds())

        t_values = list(range(0, t_max_ms + 1, step))

        if not t_values or t_values[-1] != t_max_ms:
            t_values.append(t_max_ms)
        
        capacity_values = [float(self.evaluator.capacity_at(TimeDuration(t, TimeUnit.MILLISECOND))) for t in t_values]

        return CapacityCurvePoints(
            t_ms=[float(t) for t in t_values],
            capacity=capacity_values
        )