# MessageConnector: Abstract base class for message connectors.
#
# Base interface for message connectors in the SOMA framework.
#
# Defines the MessageConnector abstract class, which specifies the required
# methods for reading, writing, and replying to messages.
#
# :author: Niels Braczek <nbraczek@bsds.de>
# :license: MIT License

from abc import abstractmethod, ABC
from typing import Iterable, Optional, Dict, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    """
    Represents a message in the SOMA system.
    This class encapsulates the details of a message, including its source type,
    source ID, subject, content, timestamp, and any additional metadata.
    The `to_dict` method converts the message to a dictionary format for easy serialization.
    """
    source_type: str = Field(
        ...,
        description="Type of the message source, e.g., 'email', 'system', 'service', etc."
    )
    source_id: str = Field(
        ...,
        description="Unique ID of the message source, e.g. `Message-Id` header in emails, used to detect duplicates"
    )
    subject: Optional[str] = Field(
        None,
        description="Subject or title of the message"
    )
    content: str = Field(
        ...,
        description="The content of the message. For emails, the entire email is stored here, including headers, HTML and text parts and attachments."
    )
    timestamp: Optional[str] = Field(
        None,
        description="ISO-date of the message"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    def clone(self) -> 'Message':
        """
        Create a clone of the current message instance.

        Returns:
            Message: A new instance of Message with the same data.
        """
        return Message(
            source_type=self.source_type,
            source_id=self.source_id,
            subject=self.subject,
            content=self.content,
            timestamp=self.timestamp,
            metadata=self.metadata.copy()
        )


class MessageConnector(ABC):
    """
    Abstract base class for message connectors.
    This class defines the interface for all message connectors in the SOMA framework.
    It requires implementations to provide methods for reading messages,
    writing messages, and replying to messages.
    Each method should be implemented by subclasses to handle specific message
    sources and formats.
    """

    @abstractmethod
    def read(self, filter: Optional[dict] = None) -> Iterable[Message]:
        """
        Read messages from the connector.

        :param filter: Optional filter criteria to apply when reading messages.
        :return: Iterable of Message objects.
        """
        ...

    @abstractmethod
    def write(self, message: Message) -> bool:
        """
        Write a message to the connector.
        :param message: The Message object to write.
        :return: True if the message was successfully written, False otherwise.
        """
        ...

    @abstractmethod
    def reply(self, original: Message, response_text: str, options: Optional[dict] = None) -> bool:
        """
        Reply to a message with a response text.
        :param original: The original Message object to which the reply is directed.
        :param response_text: The text of the reply message.
        :param options: Optional additional options for the reply. Valid options depend on the connector implementation.
        :return:  True if the reply was successfully sent, False otherwise.
        """
        ...
