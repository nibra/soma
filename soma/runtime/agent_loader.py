import re
import yaml
import structlog
from importlib import import_module
from soma.core.agent_registry import AgentRegistry
from soma.core.contracts.event_bus import EventBus


def load_agents_from_config(config_path: str, event_bus: EventBus) -> AgentRegistry:
    """
    Load and register agents from a YAML config file.
    Supports 'topics' (list) or 'topic_filter' (regex) for dynamic topic subscription.
    """
    registry = AgentRegistry()

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    logger = structlog.get_logger()

    for name, agent_conf in config.get("agents", {}).items():
        class_path = agent_conf.pop("class")
        topics = agent_conf.pop("topics", [])
        topic_filter = agent_conf.pop("topic_filter", None)

        module_path, class_name = class_path.rsplit(".", 1)
        cls = getattr(import_module(module_path), class_name)

        instance = cls(name=name, event_bus=event_bus, logger=logger, **agent_conf)
        registry.register(name, instance)

        if topics:
            for topic in topics:
                event_bus.subscribe(topic, instance)
        elif topic_filter:
            for topic in event_bus.queues.keys():
                if re.match(topic_filter, topic):
                    event_bus.subscribe(topic, instance)
        else:
            print(f"[AgentLoader] Warning: No topics or topic_filter specified for '{name}'")

        print(f"[AgentLoader] Registered agent '{name}' ({class_path})")

    return registry
