from abc import ABC, abstractmethod
from soma.core.message import Message

class EventSubscriber(ABC):
    def __init__(self, event_bus):
        """
        EventSubscriber is an abstract base class for agents that subscribe to events on an event bus.
        :param event_bus: The event bus instance to which this subscriber will be registered.
        """
        self.event_bus = event_bus

    @abstractmethod
    def handle(self, msg: Message) -> None:
        ...
