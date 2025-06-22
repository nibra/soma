# In-Memory Event Bus Implementation
#
# :author: Niels Braczek <nbraczek@bsds.de>
# :license: MIT License

import threading
import queue
import structlog
from typing import Callable, Dict, List, Optional
from soma.core.contracts.event_bus import EventBus, Subscriber, EventProducer, EventSubscriber
from soma.core.contracts.message import Message
from soma.eventbus.metrics import EVENT_LATENCY, EVENT_COUNT, EVENT_ERRORS


class InMemoryEventBus(EventBus):
    """
    InMemoryEventBus: An in-memory implementation of an event bus for testing and local use.
    This class provides a simple event bus that allows publishing and subscribing to topics
    """

    def __init__(self, **kwargs):
        """
        Initialize the InMemoryEventBus with empty queues and subscribers.
        :param policy_manager:
        """
        self.queues: Dict[str, queue.Queue] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.threads: List[threading.Thread] = []
        self.running = False
        self.policy_manager = kwargs.get("policy_manager", None)
        self.logger = kwargs.get("logger", structlog.get_logger(__name__))

        self.logger.info("InMemoryEventBus initialized", policy_manager=self.policy_manager)

    def publish(self, topic: str, message: Message, key: Optional[str] = None):
        """
        Publish a message to a specific topic on the in-memory event bus.
        :param topic: The topic to which the message should be published.
        :param message: The message to be published, typically a dictionary containing the event data.
        :param key: Optional key for the message, used for routing or identification purposes.
        :return: None
        """
        policy_violation = self.check_publish_policy(topic, message)
        if policy_violation:
            self.logger.warning(policy_violation, topic=topic, message=message)
            return

        if topic not in self.queues:
            self.queues[topic] = queue.Queue()
        self.queues[topic].put(message)

    def subscribe(self, topic: str, handler: Subscriber):
        """
        Subscribe to a specific topic on the in-memory event bus with a handler function.
        :param topic: The topic to which the handler should subscribe.
        :param handler: A callable function that will be invoked when a message is published to the topic.
        :return: None
        """
        policy_violation = self.check_subscribe_policy(topic, handler)
        if policy_violation:
            self.logger.warning(policy_violation, topic=topic, handler=handler)
            return

        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(handler)

        # Auto-inject EventBus into producer agents
        if isinstance(handler, EventProducer):
            if handler.event_bus is None:
                handler.event_bus = self

    def _consume(self, topic: str):
        """
        Consume messages from the specified topic's queue and invoke the registered handlers.
        :param topic: The topic from which to consume messages.
        :return: None
        """
        while self.running:
            try:
                msg = self.queues[topic].get(timeout=0.5)
                for subscriber in self.subscribers.get(topic, []):
                    agent_name = getattr(subscriber, "__name__", None) or getattr(subscriber, "name", "unknown")
                    try:
                        with EVENT_LATENCY.labels(topic=topic, agent=agent_name).time():
                            if isinstance(subscriber, EventSubscriber):
                                subscriber.handle(msg)
                            else:
                                subscriber(msg)

                            EVENT_COUNT.labels(topic=topic, agent=agent_name).inc()
                    except Exception as e:
                        print(f"[InMemoryEventBus] Handler error on topic '{topic}': {e}")
                        EVENT_ERRORS.labels(topic=topic, agent=agent_name).inc()
            except queue.Empty:
                continue

    def start(self):
        """
        Start the in-memory event bus, initializing consumer threads for each subscribed topic.
        :return: None
        """
        self.running = True
        for topic in self.subscribers:
            if topic not in self.queues:
                self.queues[topic] = queue.Queue()
            t = threading.Thread(target=self._consume, args=(topic,), daemon=True)
            self.threads.append(t)
            t.start()

    def stop(self):
        """
        Stop the in-memory event bus, cleaning up resources and stopping consumer threads.
        :return: None
        """
        self.running = False
        for t in self.threads:
            t.join(timeout=1.0)
        self.threads.clear()
