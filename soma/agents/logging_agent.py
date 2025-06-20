# soma/agents/logging_agent.py
import re
from soma.core.contracts.event_bus import EventSubscriber
from soma.core.contracts.message import Message
from soma.core.contracts.health import HealthStatus


class LoggingAgent(EventSubscriber):
    def __init__(self, **kwargs):
        """
        LoggingAgent is a simple agent that logs incoming messages to the console.
        :param kwargs:
        """
        self.log_prefix = kwargs.get("log_prefix", "[LoggingAgent]")
        self.topic_filter = kwargs.get("topic_filter", None)

    def handle(self, msg: Message):
        if self.topic_filter and not re.match(rf"^{self.topic_filter}$", msg.source_type):
            return
        print(f"{self.log_prefix} {msg.subject}")

    def check_health(self) -> HealthStatus:
        # Beispiel: einfacher Check auf funktionsfähige Konfiguration
        from datetime import datetime
        return HealthStatus(
            name=self.__class__.__name__,
            status="healthy",
            last_checked=datetime.now(),
            message="Ready"
        )
