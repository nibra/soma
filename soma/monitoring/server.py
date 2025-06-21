from prometheus_client import start_http_server

def start_metrics_server(port: int = 8000):
    print(f"[Metrics] Starting Prometheus metrics server on port {port}")
    start_http_server(port)
