# Massage Connector unit tests

import pytest
from soma.connectors.base import MessageConnector
from soma.core.message import Message


@pytest.mark.describe("Message Connector Interface")
class TestMessageConnector():
    @pytest.mark.it("raises NotImplementedError for unimplemented methods (read, write and reply)")
    def test_base_connector_interface(self):
        class DummyConnector(MessageConnector):
            def _(self):
                pass

        connector = DummyConnector()
        message = Message(
            source_type="test",
            source_id="test_id",
            subject="Test Subject",
            content="Test Content",
            timestamp="2023-10-01T00:00:00Z",
            metadata={}
        )

        assert hasattr(connector, 'read')
        try:
            connector.read()
        except Exception as e:
            assert isinstance(e, NotImplementedError)

        assert hasattr(connector, 'write')
        try:
            connector.write(message)
        except Exception as e:
            assert isinstance(e, NotImplementedError)

        assert hasattr(connector, 'reply')
        try:
            connector.reply(message, "reply text")
        except Exception as e:
            assert isinstance(e, NotImplementedError)
