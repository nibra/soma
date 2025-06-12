# Email Connector: Message Connector for reading and writing emails using IMAP and SMTP protocols.
#
# :author: Niels Braczek <nbraczek@bsds.de>
# :license: MIT License

from soma.core.message import Message
from soma.connectors.base import MessageConnector
from imap_tools import MailBox, AND, MailBoxUnencrypted
from typing import Optional
import smtplib
from email.mime.text import MIMEText


class EmailConnector(MessageConnector):
    """
    EmailConnector is a MessageConnector implementation for reading and writing emails using IMAP and SMTP protocols.
    """

    def __init__(self, imap_host, user, password, smtp_host=None):
        """
        Initialize the EmailConnector with IMAP and SMTP configuration.
        :param imap_host: IMAP host in the format 'schema://host:port' or 'host:port'.
        :param user: The email address or username for authentication.
        :param password: The password for the email account.
        :param smtp_host: SMTP host in the format 'schema://host:port' or 'host:port'. If None, SMTP functionality is disabled.
        """
        self.imap_schema, self.imap_host, self.imap_port = self._parse_host_port(imap_host, 143)

        if smtp_host is not None:
            self.smtp_schema, self.smtp_host, self.smtp_port = self._parse_host_port(smtp_host, 25)

        self.user = user
        self.password = password

    def read(self, filter: Optional[dict] = None) -> list[Message]:
        """
        Read unread messages from the email account using IMAP.
        :param filter: Optional filter criteria (not used in this implementation).
        :return: A list of Message objects representing unread emails.
        """
        messages = []
        if self.imap_schema == "http":
            mailbox = MailBoxUnencrypted(host=self.imap_host, port=self.imap_port)
        else:
            mailbox = MailBox(host=self.imap_host, port=self.imap_port)
        with mailbox.login(self.user, self.password, initial_folder='INBOX') as mailbox:
            for msg in mailbox.fetch(AND(seen=False)):
                headers = msg.headers
                message_id = headers["message-id"][0] if "message-id" in headers else ""
                messages.append(Message(
                    source_type="email",
                    source_id=message_id,
                    subject=msg.subject,
                    content=msg.obj.as_bytes(),
                    timestamp=msg.date.isoformat(),
                    metadata={
                        "from": msg.from_,
                        "reply_to": msg.reply_to[0] if msg.reply_to else msg.from_,
                        "in-reply-to": headers["in-reply-to"][0] if "in-reply-to" in headers else ""
                    }
                ))
        return messages

    def write(self, message: Message) -> bool:
        """
        Write a message to the email account using SMTP.
        :param message: The Message object to write.
        :return: True if the message was successfully sent, False otherwise.
        """
        if not self.smtp_host:
            raise ValueError("SMTP host is not configured for sending emails.")

        msg = MIMEText(message.content)
        msg['Subject'] = message.subject
        msg['From'] = self.user
        msg['To'] = message.source_id
        try:
            with smtplib.SMTP(host=self.smtp_host, port=self.smtp_port) as server:
                server.login(self.user, self.password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Email send error: {e}")
            return False

    def reply(self, original: Message, response_text: str, options: Optional[dict] = None) -> bool:
        """
        Reply to an email message with a response text.
        :param original: The original Message object to which the reply is directed.
        :param response_text: The text of the reply message.
        :param options: Optional additional options for the reply. Valid options depend on the connector implementation.
        :return:
        """
        if not self.smtp_host:
            raise ValueError("SMTP host is not configured for sending emails.")

        subject = options.get("subject") if options else f"Re: {original.subject}"
        to_addr = original.metadata.get("reply_to") or original.metadata.get("from")
        msg = MIMEText(response_text)
        msg['Subject'] = subject
        msg['From'] = self.user
        msg['To'] = to_addr
        msg['In-Reply-To'] = original.metadata.get("message_id")
        msg['References'] = original.metadata.get("references")
        try:
            with smtplib.SMTP(host=self.smtp_host, port=self.smtp_port) as server:
                server.login(self.user, self.password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Email reply error: {e}")
            return False

    @staticmethod
    def _parse_host_port(host: str, default_port: int) -> tuple[str, str, int]:
        """
        Parse the host and port from a given host string.
        :param host: The host string in the format 'schema://host:port' or 'host:port'.
        :param default_port: The default port to use if no port is specified in the host string.
        :return:
        """
        schema, host_and_port = host.split('://') if '://' in host else ("http", host)
        host_name, port = host_and_port.split(':') if ':' in host_and_port else (host_and_port, default_port)

        return schema, host_name, int(port)
