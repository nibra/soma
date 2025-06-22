from prometheus_client import Counter, Histogram, Gauge

EVENT_COUNT = Counter(
    "soma_events_total",
    "Total number of events processed",
    ["topic", "agent"]
)

EVENT_LATENCY = Histogram(
    "soma_event_latency_seconds",
    "Time taken to process events",
    ["topic", "agent"]
)

EVENT_ERRORS = Counter(
    "soma_event_errors_total",
    "Total number of errors encountered while processing events",
    ["topic", "agent"]
)

RATE_LIMIT_COUNTER = Counter(
    "soma_event_rate_limited_total",
    "Total number of events blocked due to rate limiting",
    ["agent", "topic"]
)

RATE_LIMIT_USAGE = Gauge(
    "soma_event_rate_limit_usage",
    "Current rate limit usage ratio (0.0 to 1.0)",
    ["agent", "topic"]
)