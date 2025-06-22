# core/governance/policy_store.py
import yaml
from typing import Dict
from soma.core.contracts.policy import AccessPolicy


class PolicyStore:
    def __init__(self, path: str):
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        self.policies: Dict[str, AccessPolicy] = {
            entry["agent"]: AccessPolicy(**entry) for entry in config.get("policies", [])
        }

    def get_policy(self, agent: str) -> AccessPolicy | None:
        return self.policies.get(agent)
