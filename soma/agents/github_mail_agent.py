import time
from datetime import datetime
from pyexpat.errors import messages
from typing import Optional

from soma.core.contracts.event_bus import EventProducer, EventSubscriber, EventBus
from soma.core.contracts.health import HealthStatus, SupportsHealthCheck
from soma.core.contracts.message import Message
from imap_tools import MailMessage
import structlog


class GitHubMailAgent(EventSubscriber, EventProducer, SupportsHealthCheck):
    def __init__(self, event_bus: EventBus, **kwargs):
        self.event_bus = event_bus
        self.name = kwargs.get("name", self.__class__.__name__)
        self.output_prefix = kwargs.get("output_prefix", "github.")
        self.logger = kwargs.get("logger", structlog.get_logger(__name__))

        self.logger.info(
            "Agent initialized",
            agent=self.name,
            output_prefix=self.output_prefix,
            event_bus=event_bus.__class__.__name__ if event_bus else "None"
        )

    def handle(self, msg: Message):
        if msg.source_type != "email":
            self.logger.debug("Ignoring non-email message", **self._log_data(msg))
            return

        if "@github.com" not in msg.metadata["from"].lower():
            self.logger.debug("Ignoring message not from GitHub", **self._log_data(msg))
            return

        self.logger.info("Incoming message", **self._log_data(msg))

        mail = MailMessage.from_bytes(msg.content.encode("utf-8"))

        message = Message(
            agent_name=self.name,
            source_type=mail.headers.get("x-github-reason", ("unknown",))[0].lower(),
            source_id=mail.headers.get("message-id", ("",))[0],
            subject=mail.subject.replace("\n", "") or "No Subject",
            content="",
            timestamp=mail.date.isoformat() if mail.date else datetime.now().isoformat(),
            metadata={
                "repository_url": mail.headers.get("list-archive", ("",))[0],
            }
        )

        if message.source_type == "ci_activity":
            return self._handle_ci_activity(mail, message)

        if message.source_type == "subscribed":
            if "A security advisory" in message.subject:
                return self._handle_security_advisory(mail, message)

            item = self._extract_issue_data(mail)
            if item is not None:
                message.metadata[item["type"]] = item["number"]
                message.metadata["url"] = item["url"]

                comment = re.search(r"^(.+?) left a comment \((.*?)\)$", item["content"], re.MULTILINE)
                if comment:
                    message.source_type = "comment." + item["type"]
                    message.content = item["content"].replace(comment.group(0), "").strip()
                    message.metadata["author"] = comment.group(1).strip()
                    return self._publish(message)

                change = re.search(rf"^(.+?) #{item['number']}", item["content"], re.MULTILINE)
                if change:
                    message.source_type = "state_change." + item["type"] + "." + change.group(1).lower()
                    message.content = item["content"]
                    return self._publish(message)

                parts = mail.text.split("You can view, comment on, or merge this pull request online at:")
                if len(parts) > 1:
                    message.content = parts[0].strip()
                    sections = re.split(r"\n-- (.*?) --\n", re.sub("\n-- \n.*", "", parts[1], flags=re.DOTALL))
                    message.metadata["url"] = sections[0].strip()
                    for i in range(1, len(sections), 2):
                        if i + 1 < len(sections) and sections[i].strip().lower() == "patch links":
                            links = sections[i + 1].strip().split("\n")
                            for link in links:
                                if not link.startswith("http"):
                                    continue
                                ext = link.split(".")[-1].lower()
                                message.metadata[ext + "_url"] = link.strip()
                    return self._publish(message)

        if message.source_type == "security_alert":
            if "Your Dependabot alerts" in message.subject:
                return self._handle_security_alert(mail, message)
            if "A security advisory" in message.subject:
                return self._handle_security_advisory(mail, message)

        if message.source_type == "state_change":
            return self._handle_state_change(mail, message)

        message.content = msg.content
        self.logger.warning("Unable to process GitHub notification", **self._log_data(msg, mail))
        self._publish(message)

    def check_health(self) -> HealthStatus:
        if self.event_bus:
            status = "healthy"
            message = "Ready"
        else:
            status = "unhealthy"
            message = "Event bus is not set or not running."
        return HealthStatus(
            name=self.name,
            status=status,
            last_checked=datetime.now(),
            message=message
        )

    def _handle_state_change(self, mail, message):
        item = self._extract_issue_data(mail)
        if item is None:
            self.logger.warning("No issue data found in message", **self._log_data(message, mail))
            return

        change = re.search(rf"^(.+?) #{item['number']}", item["content"], re.MULTILINE)
        if not change:
            self.logger.warning("No state change found in message", **self._log_data(message, mail))
            return

        message.source_type = "state_change." + item["type"] + "." + change.group(1).lower()
        message.content = item["content"]
        message.metadata[item["type"]] = item["number"]
        message.metadata["url"] = item["url"]
        return self._publish(message)

    def _handle_security_advisory(self, mail, message):
        # Handle security advisory messages
        message.source_type = "security_alert"
        dep = re.search(r"affected by a security vulnerability in (.+?)\n", mail.text)
        if not dep:
            self.logger.warning("No dependency found in security advisory", **self._log_data(message, mail))
            return

        vulnerability = re.search(rf"^(.*?severity\))\n", mail.text, re.MULTILINE)
        message.metadata["dependency"] = dep.group(1).strip()
        message.metadata["vulnerable_version"] = ""
        message.metadata["upgrade_to"] = ""
        message.metadata["vulnerabilities"] = vulnerability.group(1).strip() if vulnerability else ""
        affected = re.search(r"used in [^\n]*?:\n(.*?)\n---", mail.text, re.DOTALL)
        repos = re.split(r"(?:^|\n) {2}- (.*?)\n", affected.group(1)) if affected else []
        if len(repos) > 1:
            repos = repos[1:]
            repos = {repos[i].strip(): repos[i + 1] for i in range(0, len(repos), 2)}
        else:
            self.logger.warning("No repositories found in security advisory", **self._log_data(message, mail))
            return

        for repo in repos:
            message.metadata["repository_url"] = "https://github.com/" + repo
            message.metadata["repository"] = repo
            locations = repos[repo].split("\n")
            for location in locations:
                match = re.search(r"^Vulnerability found in (.+?) (http.+)$", location.strip("\n -"))
                if not match:
                    self.logger.warning("No vulnerability location found in security advisory", **self._log_data(message, mail))
                    continue

                message.metadata["defined_in"] = match.group(1).strip()
                message.metadata["suggested_update"] = match.group(2).strip()
                message_clone = message.clone()
                message_clone.content = ""
                self._publish(message_clone)
            else:
                self.logger.warning("No vulnerability locations found in security advisory", **self._log_data(message, mail))

    def _handle_security_alert(self, mail, message):
        """
        Handle security alert messages from Dependabot.
        This method extracts relevant information from the email content and populates the message object.
        Each vulnerability results in a separate message being published to the event bus.
        Message metadata will include:
        - `repository_url`: The URL of the repository where the alert was triggered.
        - `dependency`: The name of the vulnerable dependency.
        - `vulnerable_version`: The version of the dependency that is vulnerable.
        - `upgrade_to`: The version to which the dependency should be upgraded.
        - `defined_in`: The file where the dependency is defined.
        - `vulnerabilities`: A description of the vulnerabilities associated with the dependency.
        - `suggested_update`: A suggested update for the dependency.
        :param message: The message object to populate with security alert data.
        :param mail:  The MailMessage object containing the email content.
        :return:  None
        """
        content = mail.text
        orgs = re.split(r"(.+?) (?:organization|account)", content, re.MULTILINE)
        orgs = orgs[1:]
        orgs = {orgs[i].strip(): orgs[i + 1].strip(" -\n") for i in range(0, len(orgs), 2)}

        if not orgs:
            self.logger.warning("No organizations found in security alert", **self._log_data(message, mail))
            return

        for org, o_part in orgs.items():
            repos = re.split(r"(\n\d+\. .*?\n\n)", "\n" + o_part, re.MULTILINE)
            repos = repos[1:]
            repos = {re.sub(r"^\d+\.\s+(.*)$", r"\1", repos[i].strip()): repos[i + 1].strip(" -\n") for i in
                     range(0, len(repos), 2)}

            if not repos:
                self.logger.warning(f"No repositories found in security alert for {org}", **self._log_data(message, mail))
                continue

            for repo, r_part in repos.items():
                message.metadata["repository_url"] = repo
                deps = re.sub(r"View all vulnerable dependencies:.*$", "", r_part, flags=re.DOTALL).strip()
                deps = re.split(r"(?:^|\n)\s*(.+?) dependency\n[ -]+\n", "\n" + deps)
                deps = deps[1:]
                deps = {deps[i].strip(): deps[i + 1].strip(" -\n") for i in range(0, len(deps), 2)}

                if not deps:
                    self.logger.warning(f"No vulnerable dependencies found in security alert for {repo}", **self._log_data(message, mail))
                    continue

                for dep in deps:
                    message.metadata["dependency"] = dep
                    message.metadata["vulnerable_version"] = self._extract(deps[dep], "Vulnerable versions")
                    message.metadata["upgrade_to"] = self._extract(deps[dep], "Upgrade to")
                    message.metadata["defined_in"] = self._extract(deps[dep], "Defined in")
                    message.metadata["vulnerabilities"] = self._extract(deps[dep], "Vulnerabilities")
                    message.metadata["suggested_update"] = self._extract(deps[dep], "Suggested update")
                    self._publish(message.clone())

    def _handle_ci_activity(self, mail, message):
        """
        Handle CI activity messages from GitHub.
        This method extracts relevant information from the email content and populates the message object.
        Message metadata will include:
        - `workflow`: The name of the workflow.
        - `results`: The URL to view the results of the CI activity.
        :param message:  The message object to populate with CI activity data.
        :param mail:  The MailMessage object containing the email content.
        :return:  None
        """
        workflow = re.search(r"\nWorkflow:\s*(.+?)\n", mail.text)
        if not workflow:
            self.logger.warning("No workflow found in CI activity message", **self._log_data(message, mail))
            return
        result_url = re.search(r"View results: (.*?)\n", mail.text)
        if not result_url:
            self.logger.warning("No results URL found in CI activity message", **self._log_data(message, mail))
            return
        content = re.search(r"\* (.*? failed .*?)\n", mail.text)
        if not content:
            self.logger.warning("No relevant content found in CI activity message", **self._log_data(message, mail))
            return
        message.metadata["workflow"] = workflow.group(1)
        message.metadata["results"] = result_url.group(1)
        message.content = content.group(1)
        self._publish(message)
        return

    def _publish(self, message):
        if self.event_bus is None:
            self.logger.error("Event bus is not set. Cannot publish message.", **self._log_data(message))
            raise ValueError("Event bus is not set. Cannot publish message.")

        repository = message.metadata.get("repository_url", "")
        message.metadata["repository"] = repository.replace("https://github.com/", "")

        topic = self.output_prefix + message.source_type
        key = message.metadata.get('repository', 'unknown/unknown')

        self.logger.info("Publishing message", **self._log_data(message), topic=topic, key=key)

        self.event_bus.publish(topic, message, key=key)

    @staticmethod
    def _extract(haystack, key) -> str:
        match = re.search(rf"{key}:\s+(.+?)(?:\n|$)", haystack)
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def _extract_issue_data(mail):
        """
        Extract issue data from the email content.
        :param mail: The MailMessage object containing the email content.
        :return: A dictionary with extracted issue data or None if not found.
        """
        item = re.search(r"\((\w+) #(\d+)\)", mail.subject)
        parts = mail.text.split("-- ")
        content = parts[0].strip()
        footer = parts[1].strip() if len(parts) > 1 else ""
        url = re.search(r"https?://github\.com/\S+", footer)

        data = {}
        if item:
            data["type"] = item.group(1).lower()
            data["number"] = item.group(2)
            data["content"] = content
            data["url"] = url.group(0) if url else ""

            return data

        return None

    def _log_data(self, message: Message, mail: Optional[MailMessage] = None):
        return {
            "agent": self.name,
            "source_type": message.source_type,
            "source_id": message.source_id,
            "subject": message.subject,
            "content": mail.text[:100] + "..." if mail else message.content[:100] + "...",
            **message.metadata
        }

if __name__ == "__main__":
    import yaml
    import re
    from soma.core.registry import ConnectorRegistry
    from soma.eventbus.memory_bus import InMemoryEventBus
    from soma.runtime.ingest import ingest


    def _reset_greenmail():
        import requests
        response = requests.post("http://localhost:8080/api/service/reset")
        assert response.status_code == 200, "Failed to reset GreenMail server"


    # Initialize the logging configuration
    #import soma.logging_config
    #soma.logging_config.setup_logging()
    logger = structlog.get_logger(__name__)

    registry = ConnectorRegistry()

    _reset_greenmail()

    base_path = re.sub(r"soma/agents/.*$", "", __file__)
    with open(base_path + "/tests/fixtures/config/connectors.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    event_bus = InMemoryEventBus()
    event_bus.subscribe(
        "email",
        GitHubMailAgent(
            name="github_mail_agent",
            event_bus=event_bus,
            output_prefix="github.",
            logger=logger
        )
    )

    from soma.monitoring.server import start_metrics_server
    start_metrics_server(8000)

    event_bus.start()

    ingest(config.get("connectors", {}), event_bus)

    time.sleep(2)

    # Wait for a key press to stop the event bus
    input("Press Enter to stop the event bus...")

    event_bus.stop()
