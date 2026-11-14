
import os
from fastapi import FastAPI, Header, HTTPException

app = FastAPI(title="Traceroute Diagnostic Service")

API_TOKEN = os.getenv("API_TOKEN", "aiori-demo-token")


def verify_token(authorization):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid or missing token")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "traceroute"}


@app.get("/traceroute")
def run_traceroute(authorization: str = Header(None)):
    verify_token(authorization)

    hops = [
        {"hop": 1, "ip": "192.168.1.1", "latency_ms": 2.4},
        {"hop": 2, "ip": "10.0.0.1", "latency_ms": 8.7},
        {"hop": 3, "ip": "172.20.0.32", "latency_ms": 15.2}
    ]

    return {
        "service": "traceroute",
        "status": "success",
        "simulated": True,
        "total_hops": len(hops),
        "hops": hops
    }
