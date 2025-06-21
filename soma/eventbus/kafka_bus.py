# KafkaEventBus: Implementation of an event bus using Apache Kafka.
#
# :author: Niels Braczek <nbraczek@bsds.de>
# :license: MIT License

import threading
import json
from kafka import KafkaConsumer, KafkaProducer
from typing import Callable, Dict, List, Optional
from soma.core.contracts.event_bus import EventBus, EventProducer, EventSubscriber
from soma.core.contracts.message import Message
from soma.eventbus.metrics import EVENT_LATENCY, EVENT_COUNT, EVENT_ERRORS


class KafkaEventBus(EventBus):
    """
    KafkaEventBus: Implementation of an event bus using Apache Kafka.
    """

    def __init__(self, bootstrap_servers: str, group_id: str):
        """
        Initialize the KafkaEventBus with the given bootstrap servers and group ID.
        :param bootstrap_servers: A string representing the Kafka bootstrap servers (e.g., 'localhost:9092').
        :param group_id: A string representing the consumer group ID for this event bus.
        """
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.subscribers: Dict[str, List[Callable]] = {}
        self.consumer_threads: List[threading.Thread] = []
        self.running = False
        self.consumer_config = {
            "bootstrap_servers": self.bootstrap_servers,
            "group_id": self.group_id,
            "value_deserializer": lambda m: json.loads(m.decode("utf-8")),
            "key_deserializer": lambda k: k.decode("utf-8") if k else None,
            "auto_offset_reset": "earliest",
            "enable_auto_commit": True,
        }
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )

    def publish(self, topic: str, message: Message, key: Optional[str] = None):
        """
        Publish a message to a specific topic on the Kafka event bus.
        :param topic: The topic to which the message should be published.
        :param message: The message to be published, typically a dictionary containing the event data.
        :param key: Optional key for the message, used for routing or identification purposes.
        :return: None
        """
        self.producer.send(topic, value=message.model_dump(), key=key)
        self.producer.flush()

    def subscribe(self, topic: str, handler: Callable):
        """
        Subscribe to a specific topic on the Kafka event bus with a handler function.
        :param topic: The topic to which the handler should subscribe.
        :param handler: A callable function that will be invoked when a message is published to the topic.
        :return: None
        """
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(handler)

        # Auto-inject EventBus into producer agents
        if isinstance(handler, EventProducer):
            if handler.event_bus is None:
                handler.event_bus = self

    def _consume(self, topic: str):
        """
        Internal method to consume messages from a specific topic in a separate thread.
        :param topic: The topic from which messages should be consumed.
        :return: None
        """
        consumer = KafkaConsumer(topic, **self.consumer_config)
        while self.running:
            for msg in consumer:
                for subscriber in self.subscribers.get(topic, []):
                    agent_name = getattr(subscriber, "__name__", None) or getattr(subscriber, "name", "unknown")
                    try:
                        with EVENT_LATENCY.labels(topic=topic, agent=agent_name).time():
                            message = Message(**msg.value)

                            if isinstance(subscriber, EventSubscriber):
                                subscriber.handle(message)
                            else:
                                subscriber(message)

                            EVENT_COUNT.labels(topic=topic, agent=agent_name).inc()
                    except Exception as e:
                        print(f"[KafkaEventBus] Handler error on topic '{topic}': {e}")
                        EVENT_ERRORS.labels(topic=topic, agent=agent_name).inc()
                if not self.running:
                    break
        consumer.close()

    def start(self):
        """
        Start the Kafka event bus, initializing consumer threads for each subscribed topic.
        :return: None
        """
        self.running = True
        for topic in self.subscribers:
            t = threading.Thread(target=self._consume, args=(topic,), daemon=True)
            self.consumer_threads.append(t)
            t.start()

    def stop(self):
        """
        Stop the Kafka event bus, cleaning up resources and stopping consumer threads.
        :return: None
        """
        self.running = False
        for t in self.consumer_threads:
            t.join(timeout=1.0)
        self.consumer_threads.clear()
