# tests/integration/test_agent_loader.py

from soma.core.contracts.message import Message
from soma.eventbus.memory_bus import InMemoryEventBus
from soma.runtime.agent_loader import load_agents_from_config


def test_loads_agents_and_subscribes():
    bus = InMemoryEventBus()

    # Simulate available topics before loading agents
    bus.publish(
        "email",
        Message(
            agent_name="agent1",
            source_type="email",
            source_id="t1",
            subject="Test",
            content="",
            timestamp="now",
            metadata={}
        )
    )
    bus.publish(
        "random",
        Message(
            agent_name="agent1",
            source_type="test",
            source_id="t2",
            subject="Unmatched",
            content="",
            timestamp="now",
            metadata={}
        )
    )

    bus.start()

    registry = load_agents_from_config("tests/fixtures/config/agents.yml", bus)

    # Emit a new message to trigger agents
    bus.publish(
        "email",
        Message(
            agent_name="agent1",
            source_type="email",
            source_id="t3",
            subject="GitHub test",
            content="",
            timestamp="now",
            metadata={}
        )
    )
    bus.publish(
        "random",
        Message(
            agent_name="agent1",
            source_type="test",
            source_id="t4",
            subject="Unclassified",
            content="",
            timestamp="now",
            metadata={}
        )
    )

    import time
    time.sleep(0.3)
    bus.stop()

    assert "github_mail" in registry.all()
    assert "fallback_logger" in registry.all()
