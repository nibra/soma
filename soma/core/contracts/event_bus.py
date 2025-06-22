# EventBus: Abstract base class for event bus implementations.
#
# :author: Niels Braczek <nbraczek@bsds.de>
# :license: MIT License

from abc import ABC, abstractmethod
from typing import Union, Callable, Optional
import queue

from soma.core.contracts.message import Message
from soma.core.policy_manager import PolicyManager
from soma.eventbus.metrics import RATE_LIMIT_COUNTER, RATE_LIMIT_USAGE

Subscriber = Union[Callable[[dict], None], 'EventSubscriber']


class EventBus(ABC):
    policy_manager: Optional['PolicyManager'] = None

    """
    Abstract base class for event bus implementations.
    """
    queues: dict[str, 'queue.Queue']  # Dictionary to hold topic queues

    @abstractmethod
    def publish(self, topic: str, message: Message, key: str | None = None):
        """
        Publish a message to a specific topic on the event bus.
        :param topic: The topic to which the message should be published.
        :param message: The message to be published.
        :param key: Optional key for the message, used for routing or identification purposes.
        :return: None
        """
        ...

    @abstractmethod
    def subscribe(self, topic: str, handler: 'Subscriber'):
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

    def check_publish_policy(self, topic: str, message: Message):
        """
        Handle policy violations for publishing or subscribing.
        :param agent_name: The name of the agent involved in the policy violation.
        :param topic: The topic related to the policy violation.
        :param message: The message that caused the policy violation.
        :return: None or a string indicating the policy violation.
        """
        if self.policy_manager:
            agent_name = getattr(message, "agent_name", "anonymous_agent")

            if not self.policy_manager.is_allowed(agent_name, topic, direction="publish"):
                return f"[Policy] PUBLISH DENIED: {agent_name} not allowed to publish to '{topic}'"
            if not self.policy_manager.enforce_rate_limit(agent_name, topic):
                # Record metrics
                RATE_LIMIT_COUNTER.labels(agent=agent_name, topic=topic).inc()
                current_usage = self.policy_manager.get_usage_ratio(agent_name, topic)
                RATE_LIMIT_USAGE.labels(agent=agent_name, topic=topic).set(current_usage)

                return f"[Policy] RATE LIMIT: {agent_name} publishing too fast to '{topic}'"

        return None

    def check_subscribe_policy(self, topic: str, handler: 'Subscriber'):
        """
        Handle policy violations for subscribing.
        :param topic: The topic related to the policy violation.
        :param handler: The handler that caused the policy violation.
        :return: None or a string indicating the policy violation.
        """
        if self.policy_manager:
            agent_name = getattr(handler, "name", "anonymous_agent") if isinstance(handler, EventSubscriber) else getattr(
                handler, "__name__", "unnamed_handler")

            if not self.policy_manager.is_allowed(agent_name, topic, direction="subscribe"):
                return f"[Policy] SUBSCRIBE DENIED: {agent_name} not allowed to subscribe to '{topic}'"

        return None

class EventProducer(ABC):
    event_bus: Optional[EventBus] = None


class EventSubscriber(ABC):
    @abstractmethod
    def handle(self, msg: Message) -> None:
        ...
