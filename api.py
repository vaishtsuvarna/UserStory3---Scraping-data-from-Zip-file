import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from pipeline_monitor import DataPipelineMonitor
from pathlib import Path

app = FastAPI(title="Employee Data Pipeline API")

@app.get("/")
def root():
    """Root endpoint redirects to API docs."""
    return JSONResponse(content={
        "message": "Employee Data Pipeline API",
        "endpoints": {
            "metrics": "/metrics",
            "quality": "/quality",
            "docs": "/docs"
        }
    })

@app.get("/metrics")
def get_metrics():
    """Return the latest generated metrics. If missing, attempt generation."""
    monitor = DataPipelineMonitor()
    metrics_path = monitor.metrics_file
    if not metrics_path.exists():
        try:
            monitor.generate_daily_metrics()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    try:
        data = json.loads(metrics_path.read_text())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading metrics: {e}")
    return JSONResponse(content=data)

@app.get("/quality")
def get_quality():
    monitor = DataPipelineMonitor()
    try:
        report = monitor.data_quality_report()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(content=report)

if __name__ == '__main__':
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
