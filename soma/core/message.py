# Message class for handling messages in the SOMA system
#
# This module defines the Message class, which represents a message in the SOMA system.
#
# :author: Niels Braczek <nbraczek@bsds.de>
# :license: MIT License

from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class Message:
    """
    Represents a message in the SOMA system.
    This class encapsulates the details of a message, including its source type,
    source ID, subject, content, timestamp, and any additional metadata.
    The `to_dict` method converts the message to a dictionary format for easy serialization.
    """
    source_type: str
    source_id: str
    subject: Optional[str]
    content: str
    timestamp: Optional[str]
    metadata: Optional[Dict[str, str]]

    def to_dict(self) -> Dict[str, str]:
        """
        Convert the Message instance to a dictionary format.
        This method is useful for serialization and transmission of message data.
        :return: A dictionary representation of the Message instance.
        """
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
            "subject": self.subject or "",
            "content": self.content,
            "timestamp": self.timestamp or "",
            "metadata": self.metadata or {}
        }
