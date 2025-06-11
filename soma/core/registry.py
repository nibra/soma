# Connector Registry: A registry for managing message connectors.
#
# :author: Niels Braczek <nbraczek@bsds.de>
# :license: MIT License

from soma.connectors.base import MessageConnector


class ConnectorRegistry:
    """
    ConnectorRegistry is a registry for managing message connectors.
    """

    def __init__(self):
        """
        Initialize the ConnectorRegistry with an empty dictionary to hold connectors.
        """
        self._connectors: dict[str, MessageConnector] = {}

    def register(self, source_type: str, connector: MessageConnector):
        """
        Register a message connector for a specific source type.
        :param source_type: The type of source for which the connector is being registered (e.g., "email", "mastodon").
        :param connector: The MessageConnector instance to register.
        :return: None
        """
        self._connectors[source_type] = connector

    def get(self, source_type: str) -> MessageConnector:
        """
        Retrieve a registered message connector for a specific source type.
        :param source_type: The type of source for which the connector is being requested (e.g., "email", "mastodon").
        :return: MessageConnector instance for the specified source type.
        """
        if source_type not in self._connectors:
            raise ValueError(f"No connector registered for {source_type}")
        return self._connectors[source_type]

    def all(self) -> dict[str, MessageConnector]:
        """
        Retrieve all registered message connectors.
        :return: dict[str, MessageConnector]
        """
        return self._connectors
