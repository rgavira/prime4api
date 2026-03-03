from app.utils import parse_time_string_to_duration
from app.engine import TimeUnit
from app.engine import TimeDuration
from typing import Union, List
import numpy as np
from app.models import Rate, Quota


class BoundedRate:
    def __init__(self, rate: Rate, quota: Union[Quota, List[Quota], None] = None):
        self.rate = rate
        self.quota = []
        self.limits = [rate]

        if quota:
            quotas = [quota] if not isinstance(quota, list) else quota
            valid_quotas = []

            for q in quotas:

                if q.value <= rate.value:
                    continue
                rate_capacity = rate.value * (
                    q.period.to_milliseconds() / rate.period.to_milliseconds()
                )

                if q.value > rate_capacity:
                    continue
            
            temp_limits = [rate] + valid_quotas
            temp_br = object.__new__(BoundedRate)
            temp_br.rate = rate
            temp_br.quota = valid_quotas.copy()
            temp_br.limits = temp_limits

            capacity = temp_br.capacity_at(q.period)

            if capacity >= q.value:
                valid_quotas.append(q)
                self.limits.append(q)
            else:
                print(f"[WARNING] Quota omitted as unreachable: {q}")
            
        
        self.quota = valid_quotas

    def capacity_at(self, time_simulation: TimeDuration):

        if isinstance(time_simulation, str):
            time_simulation = parse_time_string_to_duration(time_simulation)
        
        if time_simulation.unit != TimeUnit.MILLISECOND:
            t_milliseconds = time_simulation.to_milliseconds()
        else:
            t_milliseconds = time_simulation.value
        def _calculate_capacity(t_milliseconds, limits_length):
            if limits_length >= len(self.limits):
                raise ValueError("Try with length = {}".format(len(self.limits) - 1))

            value, period = self.limits[limits_length].value, self.limits[limits_length].period.to_milliseconds()

            if limits_length == 0:
                c = value * np.floor((t_milliseconds / period) + 1)
            else:
                ni = np.floor(t_milliseconds / period)  # determines which interval number (ni) 't' belongs to
                qvalue = value * ni  # capacity due to quota
                aux = t_milliseconds - ni * period  # auxiliary variable
                cprevious = _calculate_capacity(aux, limits_length - 1)
                ramp = min(cprevious, value)  # capacity due to ramp
                c = qvalue + ramp

            return c

        if time_simulation.unit != TimeUnit.MILLISECOND:
            t_milliseconds = time_simulation.to_milliseconds()
        else:
            t_milliseconds = time_simulation.value

        return _calculate_capacity(t_milliseconds, len(self.limits) - 1)


    def capacity_during(self, end_instant: Union[str, TimeDuration], start_instant: Union[str, TimeDuration] = "0ms") -> float:
        """
        Calculates the capacity during a specified time interval.

        Args:
            end_instant (Union[str, TimeDuration]): The final time instant.
            start_instant (Union[str, TimeDuration], optional): The initial time instant. Defaults to "0ms".

        Returns:
            float: The calculated capacity during the specified interval.
        """
        if isinstance(end_instant, str):
            end_instant = parse_time_string_to_duration(end_instant)
        if isinstance(start_instant, str):
            start_instant = parse_time_string_to_duration(start_instant)

        # Convert time durations to milliseconds
        end_instant_milliseconds = end_instant.to_milliseconds()
        start_instant_milliseconds = start_instant.to_milliseconds()

        # Ensure the time interval is valid
        if end_instant_milliseconds <= start_instant_milliseconds:
            raise ValueError("end_instant must be greater than start_instant")

        # Calculate capacity at the start and end instants
        capacity_at_end = self.capacity_at(TimeDuration(end_instant_milliseconds, TimeUnit.MILLISECOND))
        capacity_at_start = self.capacity_at(TimeDuration(start_instant_milliseconds, TimeUnit.MILLISECOND))

        # Return the difference in capacity
        return capacity_at_end - capacity_at_start



if __name__ == "__main__":
    rate = Rate(value=1000, unit="req", period="1h")
    quota = Quota(value=100, unit="req", period="1day")
    bounded_rate = BoundedRate(rate)
    print(bounded_rate.capacity_at("1h"))




        


        
    