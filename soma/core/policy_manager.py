import time
from collections import defaultdict

import yaml
from typing import List, Dict, Tuple
from soma.core.contracts.policy import AccessPolicy

class PolicyManager:
    def __init__(self, policies: List[AccessPolicy] = None):
        self.policies: policies
        self.policy_by_agent: Dict[str, AccessPolicy] = {
            p.agent_name: p for p in policies
        }
        self.rate_limits: Dict[Tuple[str, str], int] = {}
        self.usage: Dict[Tuple[str, str], List[float]] = defaultdict(list)

        for policy in policies:
            for topic, rate in policy.rate_limit_per_topic.items():
                self.rate_limits[(policy.agent_name, topic)] = rate  # rate = max events/sec


    @classmethod
    def from_yaml(cls, yaml_path: str) -> "PolicyManager":
        with open(yaml_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
            policies = [AccessPolicy(**p) for p in raw]
            return cls(policies)

    def is_allowed(self, agent: str, topic: str, direction: str) -> bool:
        """
        direction: 'publish' or 'subscribe'
        """
        policy = self.policy_by_agent.get(agent)
        if not policy:
            return False

        if direction == "publish":
            return topic in policy.allowed_publish_topics
        elif direction == "subscribe":
            return topic in policy.allowed_subscribe_topics
        return False

    def enforce_rate_limit(self, agent: str, topic: str) -> bool:
        key = (agent, topic)
        now = time.time()
        rate = self.rate_limits.get(key)

        if rate is None:
            return True  # No rate limit configured

        # Limit is in events/sec => window = 1 sec
        window = 1.0
        timestamps = self.usage[key]
        timestamps = [ts for ts in timestamps if now - ts < window]
        self.usage[key] = timestamps

        if len(timestamps) < rate:
            self.usage[key].append(now)
            return True
        return False

    def get_usage_ratio(self, agent: str, topic: str) -> float:
        key = (agent, topic)
        now = time.time()
        rate = self.rate_limits.get(key)

        if rate is None:
            return 0.0

        window = 1.0
        timestamps = self.usage[key]
        timestamps = [ts for ts in timestamps if now - ts < window]
        self.usage[key] = timestamps

        return min(len(timestamps) / rate, 1.0)
