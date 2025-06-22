from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class AccessPolicy(BaseModel):
    agent_name: str  # agent name
    allowed_publish_topics: List[str] = Field(default_factory=list)
    allowed_subscribe_topics: List[str] = Field(default_factory=list)
    rate_limit_per_topic: Dict[str, int] = Field(default_factory=dict)
