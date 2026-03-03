from enum import Enum
from typing import Union

#TODO: REFACTOR THIS TO AN EFFICIENT IMPLEMENTATION (REDUCE IF STATEMENTS)

class TimeUnit(Enum):
    MILLISECOND = "ms"
    SECOND = "s"
    MINUTE = "min"
    HOUR = "h"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    
    
    def to_seconds(self, value: int = 1) -> float:
        if self == TimeUnit.MILLISECOND:
            return value / 1000
        elif self == TimeUnit.SECOND:
            return value
        elif self == TimeUnit.MINUTE:
            return value * 60
        elif self == TimeUnit.HOUR:
            return value * 3600
        elif self == TimeUnit.DAY:
            return value * 86400
        elif self == TimeUnit.WEEK:
            return value * 604800
        elif self == TimeUnit.MONTH:
            return value * 2592000
        elif self == TimeUnit.YEAR:
            return value * 31104000
        else:
            raise ValueError("Invalid time unit")
        
    def to_milliseconds(self, value: int = 1) -> float:
        if self == TimeUnit.MILLISECOND:
            return value
        elif self == TimeUnit.SECOND:
            return value * 1000
        elif self == TimeUnit.MINUTE:
            return value * 60000
        elif self == TimeUnit.HOUR:
            return value * 3600000
        elif self == TimeUnit.DAY:
            return value * 86400000
        elif self == TimeUnit.WEEK:
            return value * 604800000
        elif self == TimeUnit.MONTH:
            return value * 2592000000
        elif self == TimeUnit.YEAR:
            return value * 31104000000
        else:
            raise ValueError("Invalid time unit")
    
    def seconds_to_time_unit(self, seconds: float) -> float:
        if self == TimeUnit.MILLISECOND:
            return seconds * 1000
        elif self == TimeUnit.SECOND:
            return seconds
        elif self == TimeUnit.MINUTE:
            return seconds / 60
        elif self == TimeUnit.HOUR:
            return seconds / 3600
        elif self == TimeUnit.DAY:
            return seconds / 86400
        elif self == TimeUnit.WEEK:
            return seconds / 604800
        elif self == TimeUnit.MONTH:
            return seconds / 2592000
        elif self == TimeUnit.YEAR:
            return seconds / 31104000
        else:
            raise ValueError("Invalid time unit")
        
    def inferior_unit(self) -> "TimeUnit":
        """
        Devuelve la unidad de tiempo inmediatamente inferior a la actual.
        """
        hierarchy = [
            TimeUnit.MILLISECOND,
            TimeUnit.SECOND,
            TimeUnit.MINUTE,
            TimeUnit.HOUR,
            TimeUnit.DAY,
            TimeUnit.WEEK,
            TimeUnit.MONTH,
            TimeUnit.YEAR,
        ]
        current_index = hierarchy.index(self)
        if current_index == 0:
            raise ValueError("No inferior unit exists for MILLISECOND.")
        return hierarchy[current_index - 1]

    def to(self, target_unit: "TimeUnit", value: float = 1) -> float:
        """
        Convierte un valor de la unidad actual a la unidad de tiempo objetivo.

        Args:
            target_unit (TimeUnit): La unidad de tiempo objetivo.
            value (float): El valor a convertir.

        Returns:
            float: El valor convertido a la unidad objetivo.
        """
        # Convertir el valor a segundos primero
        value_in_seconds = self.to_seconds(value)
        # Convertir de segundos a la unidad objetivo
        return target_unit.seconds_to_time_unit(value_in_seconds)


class TimeDuration:
    def __init__(self, value: int, unit: TimeUnit):
        self.value = value
        self.unit = unit
        

    def to_seconds(self) -> float:
        return self.unit.to_seconds(self.value)
    
    def to_milliseconds(self) -> float:
        return self.unit.to_milliseconds(self.value)
    
    def to_desired_time_unit(self, target_unit: TimeUnit) -> "TimeDuration":
        """
        Convierte la duración actual a la unidad de tiempo deseada y devuelve un nuevo objeto TimeDuration.
        
        Args:
            target_unit (TimeUnit): La unidad de tiempo deseada para la conversión.
        
        Returns:
            TimeDuration: Un nuevo objeto TimeDuration con el valor convertido.
        """
    # Primero, convertimos la duración actual a segundos
        seconds = self.to_seconds()

        # Luego, convertimos los segundos a la unidad deseada
        if target_unit == TimeUnit.MILLISECOND:
            value_in_target_unit = seconds * 1000
        elif target_unit == TimeUnit.SECOND:
            value_in_target_unit = seconds
        elif target_unit == TimeUnit.MINUTE:
            value_in_target_unit = seconds / 60
        elif target_unit == TimeUnit.HOUR:
            value_in_target_unit = seconds / 3600
        elif target_unit == TimeUnit.DAY:
            value_in_target_unit = seconds / 86400
        elif target_unit == TimeUnit.WEEK:
            value_in_target_unit = seconds / 604800
        elif target_unit == TimeUnit.MONTH:
            value_in_target_unit = seconds / 2592000
        elif target_unit == TimeUnit.YEAR:
            value_in_target_unit = seconds / 31104000
        else:
            raise ValueError("Invalid target time unit")

        # Retornamos un nuevo objeto TimeDuration con la unidad deseada
        return TimeDuration(value_in_target_unit, target_unit)
    
    def __add__(self, other: "TimeDuration") -> "TimeDuration":
        """
        Suma dos instancias de TimeDuration. Convierte ambas a segundos, suma sus valores
        y devuelve un nuevo TimeDuration con la unidad de la primera instancia.
        """
        if not isinstance(other, TimeDuration):
            raise TypeError("Can only add TimeDuration to another TimeDuration")
        
        # Convertir ambas duraciones a segundos
        total_seconds = self.to_seconds() + other.to_seconds()
        
        # Convertir el total a la unidad de la primera instancia
        total_in_self_unit = self.unit.seconds_to_time_unit(total_seconds)
        return TimeDuration(total_in_self_unit, self.unit)
    
    def __sub__(self, other: "TimeDuration") -> "TimeDuration":
        """
        Resta dos instancias de TimeDuration. Convierte ambas a segundos, resta sus valores
        y devuelve un nuevo TimeDuration con la unidad de la primera instancia.
        """
        if not isinstance(other, TimeDuration):
            raise TypeError("Can only subtract TimeDuration from another TimeDuration")
        
        # Convertir ambas duraciones a segundos
        total_seconds = self.to_seconds() - other.to_seconds()
        
        # Convertir el total a la unidad de la primera instancia
        total_in_self_unit = self.unit.seconds_to_time_unit(total_seconds)
        return TimeDuration(total_in_self_unit, self.unit)

    def __mul__(self, other: Union["TimeDuration", int, float]) -> "TimeDuration":
        """
        Multiplies a TimeDuration by either another TimeDuration or a number.
        If multiplied by another TimeDuration, converts both to seconds, multiplies values
        and returns a new TimeDuration with the unit of the first instance.
        If multiplied by a number, multiplies the value directly.
        """
        if isinstance(other, TimeDuration):
            # Convertir ambas duraciones a segundos
            total_seconds = self.to_seconds() * other.to_seconds()
            # Convertir el total a la unidad de la primera instancia
            total_in_self_unit = self.unit.seconds_to_time_unit(total_seconds)
            return TimeDuration(total_in_self_unit, self.unit)
        elif isinstance(other, (int, float)):
            return TimeDuration(self.value * other, self.unit)
        else:
            raise TypeError("Can only multiply TimeDuration with another TimeDuration or a number")
    

    def __repr__(self):
        return f"{self.value} {self.unit.value}"
    
    def __round__(self, n: int = 0) -> "TimeDuration":
        return TimeDuration(round(self.value, n), self.unit)