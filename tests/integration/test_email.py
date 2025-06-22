# Email integration tests
#
# Make sure to start the Docker containers before executing these tests.
# SMTP will be available at http://localhost:3025
# IMAP will be available at http://localhost:3143
# GreenMail will be available at http://localhost:8080

import pytest
from soma.connectors.email_connector import EmailConnector
from soma.core.contracts.message import Message


@pytest.mark.describe("Email Connector")
class TestEmailConnector:
    @pytest.fixture
    def email_connector(self):
        return EmailConnector(
            smtp_host="http://localhost:3025",
            imap_host="http://localhost:3143",
            user="user1@localhost",
            password="password1"
        )

    @pytest.mark.it("initializes with SMTP and IMAP hosts, and ports, user, and password")
    def test_initialization(self, email_connector):
        assert email_connector.smtp_host == "localhost"
        assert email_connector.smtp_port == 3025
        assert email_connector.imap_host == "localhost"
        assert email_connector.imap_port == 3143
        assert email_connector.user == "user1@localhost"
        assert email_connector.password == "password1"

    @pytest.mark.it("reads emails from the IMAP server and returns a list of Message objects")
    def test_read_emails(self, email_connector):
        # Reset the GreenMail server to ensure a clean state
        self._reset_greenmail()

        messages = email_connector.read()
        assert isinstance(messages, list)
        assert len(messages) == 1, "Expected one message in the inbox after reset"
        for msg in messages:
            assert isinstance(msg, Message)
            assert msg.source_type == "email"
            assert msg.source_id == "<174931494345.2528320.11015584980533813920@atlan>"
            assert msg.subject == "Test Email"
            assert msg.content == """Content-Type: text/plain; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
From: sender@localhost
To: user1@localhost
Subject: Test Email
Date: Sat, 07 Jun 2025 18:49:03 +0200
Message-ID: <174931494345.2528320.11015584980533813920@atlan>
Reply-To: replyto@localhost

This is a test email body."""

    @staticmethod
    def _reset_greenmail():
        import requests
        response = requests.post("http://localhost:8080/api/service/reset")
        assert response.status_code == 200, "Failed to reset GreenMail server"

    @pytest.mark.it("sends an email using the SMTP server")
    def test_send_email(self, email_connector):
        message = Message(
            agent_name="agent1",
            source_type="email",
            source_id="user2@localhost",
            subject="Test Send Email",
            content="This is a test email content.",
            metadata={},
            timestamp=None
        )
        result = email_connector.write(message)
        assert result is True, "Email should be sent successfully"

    @pytest.mark.it("replies to an email using the SMTP server")
    def test_reply_email(self, email_connector):
        original_message = Message(
            agent_name="agent1",
            source_type="email",
            source_id="user1@localhost",
            subject="Test Email",
            content="This is a test email body.",
            metadata={
                "message_id": "<test-message-id>",
                "from": "sender@localhost",
                "reply_to": "replyto@localhost"
            },
            timestamp=None
        )
        response_text = "This is a reply to the test email."
        result = email_connector.reply(original_message, response_text)
        assert result is True, "Reply should be sent successfully"
