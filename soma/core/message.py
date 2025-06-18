# Message class for handling messages in the SOMA system
#
# This module defines the Message class, which represents a message in the SOMA system.
#
# :author: Niels Braczek <nbraczek@bsds.de>
# :license: MIT License

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


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
