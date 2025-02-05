from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import os

app = FastAPI()

# Get configuration from environment variables
METRIC_VALUE = os.getenv("METRIC_VALUE", "30")
METRIC_PATH = os.getenv("METRICS_PATH", "/metrics2")


@app.get(METRIC_PATH, response_class=PlainTextResponse)
async def metrics():
    return f"""# HELP my_first_metric Some description of what my_first_metric means
# TYPE my_first_metric gauge
my_first_metric {METRIC_VALUE}"""


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
