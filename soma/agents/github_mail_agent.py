# soma/agents/github_mail_agent.py
import time
from datetime import datetime
from soma.core.message import Message
from soma.agents.event_subscriber import EventSubscriber
from soma.eventbus.base import EventBus
from imap_tools import MailMessage


class GitHubMailAgent(EventSubscriber):
    def __init__(self, bus: EventBus, output_prefix="github."):
        self.bus = bus
        self.output_prefix = output_prefix

    def handle(self, msg: Message):
        if msg.source_type != "email":
            # Ignore messages not from email
            return

        if "@github.com" not in msg.metadata["from"].lower():
            # Ignore messages not from GitHub
            return

        mail = MailMessage.from_bytes(msg.content.encode("utf-8"))

        message = Message(
            source_type = mail.headers.get("x-github-reason", ("unknown",))[0].lower(),
            source_id = mail.headers.get("message-id", ("",))[0],
            subject = mail.subject or "No Subject",
            content = "",
            timestamp = mail.date.isoformat() if mail.date else datetime.now().isoformat(),
            metadata = {
                "repository_url": mail.headers.get("list-archive", ("",))[0],
            }
        )

        if message.source_type == "ci_activity":
            return self._handle_ci_activity(message, mail)

        if message.source_type == "state_change":
            content = mail.text
            return

        if message.source_type == "security_alert":
            if "Dependabot" in message.subject:
                return self._handle_security_alert_dependabot(mail, message)

            return

    def _handle_security_alert_dependabot(self, mail, message):
        content = mail.text
        orgs = re.split(r"(.+?) (?:organization|account)", content, re.MULTILINE)
        orgs = orgs[1:]
        orgs = {orgs[i].strip(): orgs[i + 1].strip(" -\n") for i in range(0, len(orgs), 2)}
        for org, o_part in orgs.items():
            repos = re.split(r"(\n\d+\. .*?\n\n)", "\n" + o_part, re.MULTILINE)
            repos = repos[1:]
            repos = {re.sub(r"^\d+\.\s+(.*)$", r"\1", repos[i].strip()): repos[i + 1].strip(" -\n") for i in
                     range(0, len(repos), 2)}

            for repo, r_part in repos.items():
                message.metadata["repository_url"] = repo
                deps = re.sub(r"View all vulnerable dependencies:.*$", "", r_part, flags=re.DOTALL).strip()

                deps = re.split(r"(?:^|\n)\s*(.+?) dependency\n[ -]+\n", "\n" + r_part)
                deps = deps[1:]
                deps = {deps[i].strip(): deps[i + 1].strip(" -\n") for i in range(0, len(deps), 2)}

                for dep in deps:
                    message.metadata["dependency"] = dep
                    message.metadata["vulnerable_version"] = self._extract(deps[dep], "Vulnerable versions")
                    message.metadata["upgrade_to"] = self._extract(deps[dep], "Upgrade to")
                    message.metadata["defined_in"] = self._extract(deps[dep], "Defined in")
                    message.metadata["vulnerabilities"] = self._extract(deps[dep], "Vulnerabilities")
                    message.metadata["suggested_update"] = self._extract(deps[dep], "Suggested update")
                    self._publish(message.clone())

    def _handle_ci_activity(self, message, mail):
        workflow = re.search(r"\nWorkflow:\s*(.+?)\n", mail.text)
        if not workflow:
            return
        result_url = re.search(r"View results: (.*?)\n", mail.text)
        if not result_url:
            return
        content = re.search(r"\* (.*? failed .*?)\n", mail.text)
        if not content:
            return
        message.metadata["workflow"] = workflow.group(1)
        message.metadata["results"] = result_url.group(1)
        message.content = content.group(1)
        self._publish(message)
        return

    def _publish(self, message):
        repository = message.metadata.get("repository_url", "")
        message.metadata["repository"] = repository.replace("https://github.com/", "")

        topic = message.source_type
        key = message.metadata.get('repository', 'unknown/unknown')

        self.bus.publish(self.output_prefix + topic, message, key=key)

    @staticmethod
    def _extract(haystack, key) -> str:
        match = re.search(rf"{key}:\s+(.+?)(?:\n|$)", haystack)
        if match:
            return match.group(1).strip()
        return ""

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


    registry = ConnectorRegistry()

    _reset_greenmail()

    base_path = re.sub(r"soma/agents/.*$", "", __file__)
    with open(base_path + "/tests/fixtures/config/connectors.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    event_bus = InMemoryEventBus()
    event_bus.subscribe("email", GitHubMailAgent(event_bus))
    event_bus.start()

    ingest({"email.git": config.get("connectors", {})["email.git"]}, event_bus)

    time.sleep(2)

    print("\nIngested messages from connectors:\n")
    for topic in event_bus.queues:
        while not event_bus.queues[topic].empty():
            message = event_bus.queues[topic].get()
            print(f"Topic: {topic}\nSubject: {message.subject}\nContent: {message.content}\nMetadata: {message.metadata}\n")

    print("Ingestion complete.")

    event_bus.stop()