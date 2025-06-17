from abc import ABC, abstractmethod
from soma.core.message import Message

class EventSubscriber(ABC):
    @abstractmethod
    def handle(self, msg: Message) -> None:
        ...
