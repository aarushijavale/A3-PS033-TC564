
import os
import sys
import time
import socket
import subprocess
import re

from io import StringIO
from contextlib import redirect_stdout
from threading import Lock

from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.abspath("client"))

from discovery_client import SERVICES, discover_service, invoke_service


# ==========================================
# FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="AIORI PS-033 Diagnostic API",
    description="DNSSEC-based diagnostic service discovery with Live Network testing",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://aiori-ps033-frontend.onrender.com",
        "https://a3-ps-033-tc-564-epculyg18-aarushi-0b18.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

execution_lock = Lock()


# ==========================================
# EXISTING LAB NETWORK ENDPOINTS
# ==========================================

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "message": "AIORI backend is running"
    }


@app.get("/api/status")
def status():
    return {
        "status": "online",
        "services": list(SERVICES.keys()),
        "discovery": "DNSSEC + SVCB + TXT"
    }


@app.post("/api/diagnostics/{service}")
def run_diagnostic(service: str):

    if service not in SERVICES:
        raise HTTPException(
            status_code=404,
            detail="Unknown diagnostic service"
        )

    output = StringIO()

    try:
        with execution_lock:
            with redirect_stdout(output):
                target, port = discover_service(service)
                result = invoke_service(service, target, port)

        return {
            "status": "success",
            "service": service,
            "logs": output.getvalue().splitlines(),
            "result": result
        }

    except Exception as error:

        raise HTTPException(
            status_code=502,
            detail={
                "status": "error",
                "service": service,
                "logs": output.getvalue().splitlines(),
                "message": str(error)
            }
        )


# ==========================================
# LIVE NETWORK DIAGNOSTICS
# ==========================================

class LiveNetworkRequest(BaseModel):
    host: str = Field(min_length=1, max_length=253)
    port: int = Field(default=443, ge=1, le=65535)


def validate_live_host(host: str):

    host = host.strip()

    if not re.fullmatch(r"[A-Za-z0-9.-]{1,253}", host):
        raise HTTPException(
            status_code=400,
            detail="Invalid hostname"
        )

    if host.startswith(".") or host.endswith("."):
        raise HTTPException(
            status_code=400,
            detail="Invalid hostname"
        )

    try:
        socket.getaddrinfo(host, None)

    except socket.gaierror:
        raise HTTPException(
            status_code=502,
            detail="DNS resolution failed"
        )

    return host


@app.get("/api/live/health")
def live_health():

    return {
        "status": "online",
        "mode": "live",
        "message": "Live network diagnostics are ready"
    }


# ==========================================
# LIVE DNS RESOLUTION
# ==========================================

@app.post("/api/live/dns")
def live_dns(request: LiveNetworkRequest):

    host = validate_live_host(request.host)

    addresses = sorted({
        item[4][0]
        for item in socket.getaddrinfo(host, None)
    })

    return {
        "status": "success",
        "test": "Live DNS Resolution",
        "host": host,
        "addresses": addresses
    }


# ==========================================
# LIVE TCP LATENCY
# ==========================================

@app.post("/api/live/latency")
def live_latency(request: LiveNetworkRequest):

    host = validate_live_host(request.host)

    timings = []
    errors = []

    for attempt in range(4):

        start = time.perf_counter()

        try:
            with socket.create_connection(
                (host, request.port),
                timeout=5
            ):

                elapsed = (
                    time.perf_counter() - start
                ) * 1000

                timings.append(round(elapsed, 2))

        except OSError as error:
            errors.append(str(error))

    if not timings:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "TCP connection failed",
                "errors": errors
            }
        )

    return {
        "status": "success",
        "test": "Live TCP Latency",
        "host": host,
        "port": request.port,
        "samples_ms": timings,
        "average_ms": round(
            sum(timings) / len(timings), 2
        ),
        "minimum_ms": min(timings),
        "maximum_ms": max(timings),
        "failed_attempts": len(errors)
    }


# ==========================================
# LIVE TRACEROUTE
# ==========================================

@app.post("/api/live/traceroute")
def live_traceroute(request: LiveNetworkRequest):

    host = validate_live_host(request.host)

    try:

        result = subprocess.run(
            [
                "traceroute",
                "-n",
                "-m", "12",
                "-w", "1",
                "-q", "1",
                host
            ],
            capture_output=True,
            text=True,
            timeout=20
        )

        return {
            "status": (
                "success"
                if result.returncode == 0
                else "partial"
            ),
            "test": "Live Traceroute",
            "host": host,
            "logs": result.stdout.splitlines(),
            "errors": result.stderr.splitlines()
        }

    except subprocess.TimeoutExpired:

        raise HTTPException(
            status_code=504,
            detail="Traceroute timed out"
        )


# ==========================================
# LIVE PATH MTU - DF PACKET PROBING
# ==========================================

@app.post("/api/live/pathmtu")
def live_pathmtu(request: LiveNetworkRequest):

    host = validate_live_host(request.host)

    low = 0
    high = 1472

    largest_confirmed = -1
    probe_results = []

    try:

        while low <= high:

            payload = (low + high) // 2

            result = subprocess.run(
                [
                    "ping",
                    "-4",
                    "-M", "do",
                    "-s", str(payload),
                    "-c", "2",
                    "-W", "1",
                    host
                ],
                capture_output=True,
                text=True,
                timeout=4
            )

            success = "bytes from" in result.stdout

            probe_results.append({
                "payload_bytes": payload,
                "packet_size_bytes": payload + 28,
                "success": success
            })

            if success:

                largest_confirmed = payload
                low = payload + 1

            else:

                high = payload - 1

        if largest_confirmed < 0:

            return {
                "status": "partial",
                "test": "Live Path MTU Discovery",
                "host": host,
                "message": (
                    "No successful DF probe. "
                    "MTU could not be measured."
                ),
                "probes": probe_results
            }

        confirmed_mtu = largest_confirmed + 28

        return {
            "status": "success",
            "test": "Live Path MTU Discovery",
            "host": host,
            "largest_confirmed_payload_bytes": largest_confirmed,
            "minimum_confirmed_mtu_bytes": confirmed_mtu,
            "measurement_limit_bytes": 1500,
            "message": (
                "At least 1500 bytes confirmed without fragmentation."
                if largest_confirmed == 1472
                else (
                    "Largest successfully confirmed packet "
                    "within the tested range."
                )
            ),
            "probes": probe_results
        }

    except subprocess.TimeoutExpired:

        raise HTTPException(
            status_code=504,
            detail="Path MTU probing timed out"
        )
