from fastapi import FastAPI, Request, Query
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from collections import deque
from datetime import datetime, timezone
import time
import uuid
import math

EMAIL = "24f2004647@ds.study.iitm.ac.in"

app = FastAPI()

START_TIME = time.time()

# Prometheus counter
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests"
)

# Keep last logs in memory
LOGS = deque(maxlen=1000)


@app.middleware("http")
async def log_and_count(request: Request, call_next):
    http_requests_total.inc()

    request_id = str(uuid.uuid4())

    entry = {
        "level": "INFO",
        "ts": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "request_id": request_id
    }

    LOGS.append(entry)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/")
def root():
    return {"status": "running"}


@app.get("/work")
def work(n: int = Query(..., ge=0)):
    # Simulate K units of work
    for _ in range(n):
        pass

    return {
        "email": EMAIL,
        "done": n
    }


@app.get("/healthz")
def healthz():
    uptime = time.time() - START_TIME

    if not math.isfinite(uptime):
        uptime = 0.0

    return {
        "status": "ok",
        "uptime_s": float(uptime)
    }


@app.get("/logs/tail")
def logs_tail(limit: int = 10):
    limit = max(0, min(limit, 1000))
    return list(LOGS)[-limit:]


@app.get("/metrics")
def metrics():
    return PlainTextResponse(
        generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST
    )
