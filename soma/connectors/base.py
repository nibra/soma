# MessageConnector: Abstract base class for message connectors.
#
# Base interface for message connectors in the SOMA framework.
#
# Defines the MessageConnector abstract class, which specifies the required
# methods for reading, writing, and replying to messages.
#
# :author: Niels Braczek <nbraczek@bsds.de>
# :license: MIT License

from typing import Iterable, Optional
from soma.core.message import Message


class MessageConnector:
    """
    Abstract base class for message connectors.
    This class defines the interface for all message connectors in the SOMA framework.
    It requires implementations to provide methods for reading messages,
    writing messages, and replying to messages.
    Each method should be implemented by subclasses to handle specific message
    sources and formats.
    """

    def read(self, filter: Optional[dict] = None) -> Iterable[Message]:
        """
        Read messages from the connector.

        :param filter: Optional filter criteria to apply when reading messages.
        :return: Iterable of Message objects.
        """
        raise NotImplementedError

    def write(self, message: Message) -> bool:
        """
        Write a message to the connector.
        :param message: The Message object to write.
        :return: True if the message was successfully written, False otherwise.
        """
        raise NotImplementedError

    def reply(self, original: Message, response_text: str, options: Optional[dict] = None) -> bool:
        """
        Reply to a message with a response text.
        :param original: The original Message object to which the reply is directed.
        :param response_text: The text of the reply message.
        :param options: Optional additional options for the reply. Valid options depend on the connector implementation.
        :return:  True if the reply was successfully sent, False otherwise.
        """
        raise NotImplementedError
