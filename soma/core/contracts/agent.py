from typing import List, Dict
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict

from soma.core.contracts.event_bus import EventSubscriber


class AgentEntry(BaseModel):
    name: str
    instance: EventSubscriber
    topics: list[str] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentMetadata(BaseModel):
    agent_id: str = Field(default_factory=lambda: str(uuid4()), description="Globally unique agent identifier")
    name: str = Field(..., description="Human-readable name of the agent")
    agent_class: str = Field(..., description="Python import path or type of the agent implementation")
    subscriptions: List[str] = Field(..., description="Topics the agent subscribes to")
    emits: List[str] = Field(..., description="Topics the agent publishes messages to")
    description: str = Field(default="", description="Optional description of the agent")
    status: str = Field(default="initialized", description="Agent status: e.g., 'initialized', 'running', 'stopped'")
    protocols: List[str] = Field(default_factory=lambda: ["internal.eventbus"],
                                 description="Communication protocols used by the agent")
    extensions: Dict = Field(default_factory=dict, description="Additional metadata or configuration values")
