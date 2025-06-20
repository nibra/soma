# soma/core/agent_registry.py

from typing import Dict
from pydantic import BaseModel, ConfigDict
from soma.agents.event_subscriber import EventSubscriber


class AgentEntry(BaseModel):
    name: str
    instance: EventSubscriber
    topics: list[str] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentRegistry:
    """
    A global registry for managing agent instances.
    """
    def __init__(self):
        self._agents: Dict[str, AgentEntry] = {}

    def register(self, name: str, agent: EventSubscriber):
        """
        Register an agent instance under a unique name.
        """
        if name in self._agents:
            raise ValueError(f"Agent with name '{name}' is already registered")
        self._agents[name] = AgentEntry(name=name, instance=agent)

    def get(self, name: str) -> EventSubscriber:
        """
        Retrieve a registered agent by name.
        """
        if name not in self._agents:
            raise KeyError(f"No agent registered under name '{name}'")
        return self._agents[name].instance

    def all(self) -> Dict[str, AgentEntry]:
        """
        Return all registered agents.
        """
        return self._agents
