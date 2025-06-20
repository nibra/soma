from soma.core.registry import ConnectorRegistry
from importlib import import_module
from soma.eventbus.memory_bus import InMemoryEventBus


def ingest(config, event_bus):
    """
    Ingest messages from various connectors and send them to a Kafka topic.
    :param config:
    :param event_bus:
    :return: None
    """
    registry = ConnectorRegistry()
    for name, conf in config.items():
        cls_path = conf.pop("class")
        print(f"[ingest] Registering connector '{name}' with class '{cls_path}'")
        module_path, class_name = cls_path.rsplit(".", 1)
        connector_cls = getattr(import_module(module_path), class_name)
        connector = connector_cls(**conf)
        registry.register(name, connector)

    for name, connector in registry.all().items():
        print(f"[ingest] Reading messages from connector '{name}'")
        messages = connector.read()
        # noinspection PyTypeChecker
        print(f"[ingest] Connector '{name}' read {len(messages)} messages.")
        for msg in messages:
            event_bus.publish(
                topic=name.split(".")[0],
                message=msg,
                key="raw"
            )


if __name__ == "__main__":
    import yaml
    import re


    def _reset_greenmail():
        import requests
        response = requests.post("http://localhost:8080/api/service/reset")
        assert response.status_code == 200, "Failed to reset GreenMail server"


    _reset_greenmail()

    base_path = re.sub(r"soma/runtime/.*$", "", __file__)
    with open(base_path + "/tests/fixtures/config/connectors.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    event_bus = InMemoryEventBus()

    ingest(config.get("connectors", {}), event_bus)

    print("Ingested messages from connectors:")
    for topic in event_bus.queues:
        while not event_bus.queues[topic].empty():
            message = event_bus.queues[topic].get()
            print(f"Topic: {topic}, Message: {message}")
    print("Ingestion complete.")
