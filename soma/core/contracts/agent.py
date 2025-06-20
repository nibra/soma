from typing import List, Dict
from pydantic import BaseModel, Field, ConfigDict

from soma.core.contracts.event_bus import EventSubscriber


class AgentEntry(BaseModel):
    name: str
    instance: EventSubscriber
    topics: list[str] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentMetadata(BaseModel):
    name: str
    cls: str  # fx. "soma.agents.github_mail_agent.GitHubMailAgent"
    input_topics: List[str]
    output_topics: List[str]
    description: str = ""
    status: str = Field(default="initialized", description="fx. 'initialized', 'running', 'stopped'")
    extra: Dict = Field(default_factory=dict)
