# Connector Registry unit tests
from soma.core.contracts.message import MessageConnector
from soma.core.registry import ConnectorRegistry
import pytest


class DummyConnector(MessageConnector):
    def read(self, **kwargs): return []

    def write(self, message): pass

    def reply(self, message, response_text, **kwargs): pass


class AnotherDummyConnector(MessageConnector):
    def read(self, **kwargs): return []

    def write(self, message): pass

    def reply(self, message, response_text, **kwargs): pass


@pytest.mark.describe("Connector Registry")
class TestConnectorRegistry:
    @pytest.mark.it("registers and resolves connectors with the specified name")
    def test_registry_register_and_resolve(self):
        connector = DummyConnector()
        registry = ConnectorRegistry()
        registry.register("dummy", connector)
        connector_cls = registry.get("dummy")
        assert isinstance(connector_cls, MessageConnector)

    @pytest.mark.it("raises ValueError when trying to retrieve a non-registered connector")
    def test_registry_get_nonexistent(self):
        registry = ConnectorRegistry()
        try:
            registry.get("nonexistent")
        except ValueError as e:
            assert str(e) == "No connector registered for nonexistent"

    @pytest.mark.it("returns all registered connectors as a list of MessageConnectors indexed by their names")
    def test_registry_multiple_connectors(self):
        registry = ConnectorRegistry()
        registry.register("dummy", DummyConnector())
        registry.register("another_dummy", AnotherDummyConnector())
        all_connectors = registry.all()

        assert len(all_connectors) == 2
        assert "dummy" in all_connectors
        assert "another_dummy" in all_connectors
        assert isinstance(all_connectors["dummy"], MessageConnector)
