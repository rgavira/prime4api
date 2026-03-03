from typing import Optional
from app.engine import TimeUnit
from typing import Union
from app.engine import TimeDuration
from app.models import Quota
import numpy as np
from app.utils.time_utils import *

class QuotaEvaluator:

    def __init__(self, quota: Quota):
        self.quota = quota

    def capacity_at(self, t: Union[str, TimeDuration]):
        if isinstance(t, str):
            t = parse_time_string_to_duration(t)
        
        if t.unit != TimeUnit.MILLISECOND:
            t_milliseconds = t.to_milliseconds()
        else:
            t_milliseconds = t.value
    
        value, period = self.quota.value, self.quota.period
        
        c = value * np.floor((t_milliseconds / period)+1)
        
        return c


    def capacity_during(self, end_instant: Union[str, TimeDuration], start_instant: Union[str, TimeDuration] = "0ms"):

        if isinstance(end_instant, str):
            end_instant = parse_time_string_to_duration(end_instant)
        if isinstance(start_instant, str):
            start_instant = parse_time_string_to_duration(start_instant)

        end_instant_milliseconds = end_instant.to_milliseconds()
        start_instant_milliseconds = start_instant.to_milliseconds()

        if end_instant_milliseconds <= start_instant_milliseconds:
            raise ValueError("end_instant must be greater than start_instant")

        capacity_at_end = self.capacity_at(TimeDuration(end_instant_milliseconds, TimeUnit.MILLISECOND))
        capacity_at_start = self.capacity_at(TimeDuration(start_instant_milliseconds, TimeUnit.MILLISECOND))

        return capacity_at_end - capacity_at_start
    
    def min_time(self, capacity_goal: int, return_unit: Optional[TimeUnit] = None, display = True) -> Union[str, TimeDuration]:

        if capacity_goal < 0:
            raise ValueError("The 'capacity goal' should be greater or equal to 0.")
        
        T = np.floor((capacity_goal - 1) * self.quota.period.to_milliseconds() / self.quota.value) if capacity_goal > 0 else 0
        
        result_duration = TimeDuration(int(T), TimeUnit.MILLISECOND)
        
        if T == 0:
            return "0s"
        
        if return_unit is None:
            return_unit = self.quota.period.unit
        
        duration_desired = result_duration.to_desired_time_unit(return_unit)
        
        return format_time_with_unit(duration_desired) if display else duration_desired