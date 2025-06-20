# soma/agents/logging_agent.py
import re

from soma.agents.event_subscriber import EventSubscriber
from soma.core.message import Message


class LoggingAgent(EventSubscriber):
    def __init__(self, event_bus, **kwargs):
        """
        LoggingAgent is a simple agent that logs incoming messages to the console.
        :param kwargs:
        """
        super().__init__(event_bus)
        self.log_prefix = kwargs.get("log_prefix", "[LoggingAgent]")
        self.topic_filter = kwargs.get("topic_filter", None)

    def handle(self, msg: Message):
        if self.topic_filter and not re.match(rf"^{self.topic_filter}$", msg.source_type):
            return
        print(f"{self.log_prefix} {msg.subject}")
