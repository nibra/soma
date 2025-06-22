# Event Bus integration tests
#
# Make sure to start the Docker containers before executing these tests.
# Kafka will be available at http://localhost:9092

import time
import pytest
from soma.core.contracts.message import Message
from soma.eventbus.memory_bus import InMemoryEventBus
from soma.eventbus.kafka_bus import KafkaEventBus


@pytest.mark.describe("Event Bus")
class TestEventBus:
    # noinspection PyPep8Naming
    @staticmethod
    def _getInMemoryEventBus():
        return InMemoryEventBus()

    # noinspection PyPep8Naming
    def _getKafkaEventBus(self):
        from kafka.admin import KafkaAdminClient, NewTopic
        from kafka.errors import TopicAlreadyExistsError, UnknownTopicOrPartitionError

        topics = ["topic1", "topic2"]

        admin = KafkaAdminClient(bootstrap_servers="localhost:9092")
        try:
            admin.delete_topics(topics=topics)
        except UnknownTopicOrPartitionError:
            pass  # Ignore if topics do not exist

        # Wait until topics are deleted
        self.wait(lambda: any(t in admin.list_topics() for t in topics), 5)

        new_topics = [NewTopic(name=t, num_partitions=1, replication_factor=1) for t in topics]
        try:
            admin.create_topics(new_topics)
            # Wait until topics are created
            self.wait(lambda: not all(t in admin.list_topics() for t in topics), 5)
        except TopicAlreadyExistsError:
            pass

        admin.close()

        return KafkaEventBus(bootstrap_servers="localhost:9092", group_id="soma-group")

    @staticmethod
    def wait(condition, timeout_seconds):
        timeout = time.time() + timeout_seconds  # wait up to 5 seconds
        while condition() and time.time() < timeout:
            time.sleep(0.5)

    @pytest.mark.it("publishes and subscribes to messages assigned to topics")
    @pytest.mark.parametrize("bus_type", [
        "InMemoryEventBus",
        "KafkaEventBus"
    ])
    def test_publish_and_subscribe(self, bus_type):
        received = []

        def handler_1(msg):
            received.append(("handler1", msg))

        def handler_2(msg):
            received.append(("handler2", msg))

        get_event_bus = "_get" + bus_type
        bus = getattr(self, get_event_bus)()

        bus.subscribe("topic1", handler_1)
        bus.subscribe("topic1", handler_2)
        bus.subscribe("topic2", lambda msg: received.append(("handler3", msg)))

        bus.start()

        message1 = Message(
            agent_name="agent1",
            source_type="test",
            source_id="test-message-1",
            content="This is a test message 1",
            metadata={"value": 42}
        )
        message2 = Message(
            agent_name="agent1",
            source_type="test",
            source_id="test-message-2",
            content="This is a test message 2",
            metadata={"status": "ok"}
        )
        bus.publish("topic1", message1)
        bus.publish("topic2", message2)

        self.wait(lambda: len(received) < 3, 5)

        bus.stop()

        expected = [
            ("handler1", message1),
            ("handler2", message1),
            ("handler3", message2),
        ]
        assert all(item in received for item in expected)
        assert len(received) == 3
