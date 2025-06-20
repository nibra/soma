from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Literal
from datetime import datetime


class HealthStatus(BaseModel):
    name: str
    status: Literal["healthy", "degraded", "unhealthy"]
    last_checked: datetime
    message: str = ""


class SupportsHealthCheck(ABC):
    @abstractmethod
    def check_health(self) -> HealthStatus:
        ...
