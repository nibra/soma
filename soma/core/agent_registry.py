from typing import Dict, Union
from datetime import datetime

from soma.core.contracts.agent import AgentEntry, AgentMetadata
from soma.core.contracts.event_bus import EventSubscriber
from soma.core.contracts.health import HealthStatus, SupportsHealthCheck


class AgentRegistry:
    """
    A global registry for managing agent instances.
    """

    def __init__(self):
        self._agents: Dict[str, AgentEntry] = {}

    def register(self, name: str, agent: Union[EventSubscriber | AgentMetadata]) -> None:
        """
        Register an agent instance under a unique name.
        """
        if name in self._agents:
            raise ValueError(f"Agent with name '{name}' is already registered")

        if isinstance(agent, AgentMetadata):
            # If agent is metadata, we need to instantiate it
            from importlib import import_module

            module_path, class_name = agent.cls.rsplit(".", 1)
            cls = getattr(import_module(module_path), class_name)
            agent_instance = cls(event_bus=None)
        else:
            agent_instance = agent

        self._agents[name] = AgentEntry(name=name, instance=agent_instance)

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

    def get_health_statuses(self) -> list[HealthStatus]:
        statuses = []
        for entry in self._agents.values():
            agent = entry.instance
            if isinstance(agent, SupportsHealthCheck):
                try:
                    statuses.append(agent.check_health())
                except Exception as e:
                    statuses.append(HealthStatus(
                        name=entry.name,
                        status="unhealthy",
                        last_checked=datetime.now(),
                        message=str(e)
                    ))
            else:
                statuses.append(HealthStatus(
                    name=entry.name,
                    status="degraded",
                    last_checked=datetime.now(),
                    message="No health check implemented"
                ))
        return statuses


if __name__ == "__main__":
    registry = AgentRegistry()
    registry.register("github-mail", AgentMetadata(
        name="github-mail",
        cls="soma.agents.github_mail_agent.GitHubMailAgent",
        input_topics=["email"],
        output_topics=["ci_activity", "security_alert"],
        description="Parsing GitHub notifications from emails",
    ))

    print(registry.all())

    # test_health.py

    for status in registry.get_health_statuses():
        print(f"{status.name}: {status.status} ({status.message})")
