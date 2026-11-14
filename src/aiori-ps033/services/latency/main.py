
import os
import time
from fastapi import FastAPI, Header, HTTPException

app = FastAPI(title="Latency Diagnostic Service")

API_TOKEN = os.getenv("API_TOKEN", "aiori-demo-token")


def verify_token(authorization):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid or missing token")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "latency"}


@app.get("/latency")
def measure_latency(authorization: str = Header(None)):
    verify_token(authorization)

    start = time.perf_counter()
    time.sleep(0.02)
    elapsed = (time.perf_counter() - start) * 1000

    return {
        "service": "latency",
        "status": "success",
        "latency_ms": round(elapsed, 2),
        "unit": "milliseconds"
    }
