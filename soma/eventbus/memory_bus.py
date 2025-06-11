# In-Memory Event Bus Implementation
#
# :author: Niels Braczek <nbraczek@bsds.de>
# :license: MIT License

import threading
import queue
from typing import Callable, Dict, List, Optional
from soma.eventbus.base import EventBus


class InMemoryEventBus(EventBus):
    """
    InMemoryEventBus: An in-memory implementation of an event bus for testing and local use.
    This class provides a simple event bus that allows publishing and subscribing to topics
    """

    def __init__(self):
        """
        Initialize the InMemoryEventBus with empty queues and subscribers.
        """
        self.queues: Dict[str, queue.Queue] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.threads: List[threading.Thread] = []
        self.running = False

    def publish(self, topic: str, message: dict, key: Optional[str] = None):
        """
        Publish a message to a specific topic on the in-memory event bus.
        :param topic: The topic to which the message should be published.
        :param message: The message to be published, typically a dictionary containing the event data.
        :param key: Optional key for the message, used for routing or identification purposes.
        :return: None
        """
        if topic not in self.queues:
            self.queues[topic] = queue.Queue()
        self.queues[topic].put(message)

    def subscribe(self, topic: str, handler: Callable):
        """
        Subscribe to a specific topic on the in-memory event bus with a handler function.
        :param topic: The topic to which the handler should subscribe.
        :param handler: A callable function that will be invoked when a message is published to the topic.
        :return: None
        """
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(handler)

    def _consume(self, topic: str):
        """
        Consume messages from the specified topic's queue and invoke the registered handlers.
        :param topic: The topic from which to consume messages.
        :return: None
        """
        while self.running:
            try:
                msg = self.queues[topic].get(timeout=0.5)
                for handler in self.subscribers.get(topic, []):
                    try:
                        handler(msg)
                    except Exception as e:
                        print(f"[InMemoryEventBus] Handler error on topic '{topic}': {e}")
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
