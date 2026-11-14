
import os
from fastapi import FastAPI, Header, HTTPException

app = FastAPI(title="Path MTU Diagnostic Service")

API_TOKEN = os.getenv("API_TOKEN", "aiori-demo-token")


def verify_token(authorization):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid or missing token")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "pathmtu"}


@app.get("/path-mtu")
def check_path_mtu(authorization: str = Header(None)):
    verify_token(authorization)

    return {
        "service": "pathmtu",
        "status": "success",
        "simulated": True,
        "path_mtu": 1500,
        "unit": "bytes",
        "recommended_mtu": 1500
    }
