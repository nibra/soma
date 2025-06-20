from pydantic import BaseModel, Field
from typing import List, Dict

class AgentMetadata(BaseModel):
    name: str
    cls: str  # fx. "soma.agents.github_mail_agent.GitHubMailAgent"
    input_topics: List[str]
    output_topics: List[str]
    description: str = ""
    status: str = Field(default="initialized", description="fx. 'initialized', 'running', 'stopped'")
    extra: Dict = Field(default_factory=dict)

class AgentRegistry:
    def __init__(self):
        self._registry: Dict[str, AgentMetadata] = {}

    def register(self, agent: AgentMetadata):
        self._registry[agent.name] = agent
        print(f"[AgentRegistry] Registered agent '{agent.name}'")

    def deregister(self, name: str):
        if name in self._registry:
            del self._registry[name]
            print(f"[AgentRegistry] Deregistered agent '{name}'")

    def get(self, name: str) -> AgentMetadata:
        return self._registry.get(name)

    def all(self) -> List[AgentMetadata]:
        return list(self._registry.values())

    def list_names(self) -> List[str]:
        return list(self._registry.keys())

if __name__ == "__main__":
    registry = AgentRegistry()
    registry.register(AgentMetadata(
        name="github-mail",
        cls="soma.agents.github_mail_agent.GitHubMailAgent",
        input_topics=["email"],
        output_topics=["ci_activity", "security_alert"],
        description="Parsing GitHub notifications from emails",
    ))

    print(registry.all())
