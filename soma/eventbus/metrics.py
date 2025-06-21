from prometheus_client import Counter, Histogram

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
