# EventBus: Abstract base class for event bus implementations.
#
# :author: Niels Braczek <nbraczek@bsds.de>
# :license: MIT License

from abc import ABC, abstractmethod


class EventBus(ABC):
    """
    Abstract base class for event bus implementations.
    """

    @abstractmethod
    def publish(self, topic: str, message: dict, key: str | None = None):
        """
        Publish a message to a specific topic on the event bus.
        :param topic: The topic to which the message should be published.
        :param message: The message to be published, typically a dictionary containing the event data.
        :param key: Optional key for the message, used for routing or identification purposes.
        :return: None
        """
        ...

    @abstractmethod
    def subscribe(self, topic: str, handler: callable):
        """
        Subscribe to a specific topic on the event bus with a handler function.
        :param topic: The topic to which the handler should subscribe.
        :param handler: A callable function that will be invoked when a message is published to the topic.
        :return: None
        """
        ...

    @abstractmethod
    def start(self):
        """
        Start the event bus, initializing any necessary resources or connections.
        :return: None
        """
        ...

    @abstractmethod
    def stop(self):
        """
        Stop the event bus, cleaning up any resources or connections.
        :return: None
        """
        ...
