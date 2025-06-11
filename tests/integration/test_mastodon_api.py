# Mastodon API integration tests
#
# Make sure to start the Docker containers before executing these tests.
# Mastodon will be available at http://localhost:3001

import pytest
from soma.connectors.mastodon_connector import MastodonConnector
from soma.core.message import Message


@pytest.mark.describe("Mastodon Connector")
class TestMastodonConnector:
    @pytest.fixture
    def mastodon_connector(self):
        return MastodonConnector(
            instance_url="http://localhost:3001",
            access_token="your_access_token_here"
        )

    @pytest.mark.it("reads toots from Mastodon with a specific hashtag and returns them as a list of Message objects")
    def test_mastodon_read(self, mastodon_connector):
        messages = mastodon_connector.read({"hashtag": "test"})
        assert isinstance(messages, list)
        assert len(messages) == 2
        assert all(isinstance(msg, Message) for msg in messages)
        assert all(msg.source_type == "mastodon" for msg in messages)
        assert all("hashtag" in msg.metadata for msg in messages)
