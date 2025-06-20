# Mastodon Connector: Message Connector for reading and writing messages on Mastodon instances.
#
# :author: Niels Braczek <nbraczek@bsds.de>
# :license: MIT License
import json
from typing import Optional
import requests

from soma.core.contracts.message import Message, MessageConnector


class MastodonConnector(MessageConnector):
    """
    MastodonConnector is a MessageConnector implementation for reading and writing messages on Mastodon instances.
    """

    def __init__(self, instance_url: str, access_token: str):
        """
        Initialize the MastodonConnector with the instance URL and access token.
        :param instance_url: The base URL of the Mastodon instance (e.g., 'https://mastodon.example.com').
        :param access_token: The access token for authenticating API requests.
        """
        self.instance_url = instance_url
        self.token = access_token

    def read(self, filter: Optional[dict] = None) -> list[Message]:
        """
        Read messages from the Mastodon instance based on the provided filter.
        :param filter: Optional filter criteria to apply when reading messages.
        :return: A list of Message objects representing the messages read from the Mastodon instance.
        """
        hashtag = filter.get("hashtag") if filter else "public"
        url = f"{self.instance_url}/api/v1/timelines/tag/{hashtag}"
        headers = {"Authorization": f"Bearer {self.token}"}
        messages = []
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            return messages
        for post in resp.json():
            in_reply_to_id = post.get("in_reply_to_id", "")
            messages.append(Message(
                source_type="mastodon",
                source_id=post["id"],
                subject=None,
                content=json.dumps(post, ensure_ascii=False),
                timestamp=post["created_at"],
                metadata={
                    "url": post["url"],
                    "hashtag": hashtag,
                    "from": post["account"]["acct"],
                    "in_reply_to_id": in_reply_to_id if in_reply_to_id else "",
                }
            ))
        return messages

    def write(self, message: Message) -> bool:
        """
        Write a message to the Mastodon instance.
        :param message: The Message object to write.
        :return: True if the message was successfully written, False otherwise.
        """
        url = f"{self.instance_url}/api/v1/statuses"
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {"status": message.content}
        try:
            r = requests.post(url, headers=headers, data=data)
            return r.status_code == 200
        except Exception as e:
            print(f"Mastodon write error: {e}")
            return False

    def reply(self, original: Message, response_text: str, options: Optional[dict] = None) -> bool:
        """
        Reply to a message on the Mastodon instance.
        :param original: The original Message object to which the reply is directed.
        :param response_text: The text of the reply message.
        :param options: Optional additional options for the reply. Valid options depend on the connector implementation.
        :return: True if the reply was successfully sent, False otherwise.
        """
        url = f"{self.instance_url}/api/v1/statuses"
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {
            "status": f"@{original.source_id} {response_text}",
            "in_reply_to_id": original.metadata.get("post_id")
        }
        try:
            r = requests.post(url, headers=headers, data=data)
            return r.status_code == 200
        except Exception as e:
            print(f"Mastodon reply error: {e}")
            return False
