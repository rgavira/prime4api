from app.engine.time_models import TimeDuration
from pydantic import BaseModel, field_validator, ConfigDict
from app.utils.time_utils import parse_time_string_to_duration

class Quota(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    value: int
    unit: str
    period: TimeDuration
    
    @field_validator("period", mode="before")
    @classmethod
    def parse_period(cls, period_value):
        if isinstance(period_value, str):
            return parse_time_string_to_duration(period_value.strip())
        return period_value



