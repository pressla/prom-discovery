from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os

app = FastAPI()

# Get configuration from environment variables with defaults
METRICS_PATH = os.getenv("METRICS_PATH", "/metrics2")
TARGET_NAMESPACE = os.getenv("TARGET_NAMESPACE", "default")
TARGET_PORT = os.getenv("TARGET_PORT", "9090")
TARGET_SELECTOR = os.getenv("TARGET_SELECTOR", "app=metrics-server")


@app.get("/targets", response_class=JSONResponse)
async def get_targets():
    # In a real implementation, you would:
    # 1. Use the Kubernetes API to discover pods matching the selector in the specified namespace
    # 2. Format their IPs and ports as targets for Prometheus

    # For demonstration, returning static targets
    # In production, use the kubernetes client library to discover pods dynamically
    targets = [
        {
            "targets": [
                "metrics-server-1.default.svc.cluster.local:9090",
                "metrics-server-2.default.svc.cluster.local:9090",
            ],
            "labels": {
                "__metrics_path__": METRICS_PATH,
                "kubernetes_namespace": TARGET_NAMESPACE,
            },
        }
    ]

    return targets


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
