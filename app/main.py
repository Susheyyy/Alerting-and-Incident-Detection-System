import time
import random
from fastapi import FastAPI, Response, status
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST
)

app = FastAPI(title="Alerting & Incident Detection Monitored App")

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total count of HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0]
)

APP_HEALTH_STATUS = Gauge(
    "app_health_status",
    "Status of application: 1 for healthy, 0 for unhealthy"
)
APP_HEALTH_STATUS.set(1)

ACTIVE_CONNECTIONS = Gauge(
    "app_active_connections",
    "Current active simulated user connections"
)
ACTIVE_CONNECTIONS.set(5)

simulated_delay = 0.0
simulate_errors = False

@app.middleware("http")
async def prometheus_middleware(request, call_next):
    start_time = time.time()
    endpoint = request.url.path

    if endpoint == "/metrics":
        return await call_next(request)

    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = time.time() - start_time
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)

@app.get("/")
def read_root():
    if simulate_errors and random.random() < 0.6:
        return Response(content='{"status": "Internal Error Simulated"}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, media_type="application/json")
    if simulated_delay > 0:
        time.sleep(simulated_delay)
    return {"message": "System Operational", "status": "UP", "simulated_delay_sec": simulated_delay}

@app.get("/api/items")
def get_items():
    if simulate_errors and random.random() < 0.5:
        return Response(content='{"error": "Database Connection Timeout"}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, media_type="application/json")
    if simulated_delay > 0:
        time.sleep(simulated_delay + random.uniform(0.01, 0.05))
    return {"items": ["item1", "item2", "item3"], "count": 3}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "application"}

@app.post("/chaos/latency")
def set_latency(delay: float = 0.8):
    """Introduce latency to trigger HighLatency alert (> 500ms)"""
    global simulated_delay
    simulated_delay = delay
    return {"message": f"Simulated latency set to {delay} seconds"}

@app.post("/chaos/reset")
def reset_chaos():
    """Reset all chaos simulations"""
    global simulated_delay, simulate_errors
    simulated_delay = 0.0
    simulate_errors = False
    APP_HEALTH_STATUS.set(1)
    return {"message": "All chaos injection reset to normal operation"}

@app.post("/chaos/errors")
def toggle_errors(enable: bool = True):
    """Toggle 500 errors to test error rate metrics"""
    global simulate_errors
    simulate_errors = enable
    return {"message": f"Error simulation set to {enable}"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
