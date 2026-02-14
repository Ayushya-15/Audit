"""API routes for ML model management."""

import numpy as np
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Telemetry
from app.models.schemas import MLModelStatus, MLPrediction
from app.ml.model_manager import model_manager

router = APIRouter(prefix="/api/ml", tags=["ml"])


@router.get("/status", response_model=list[dict])
def get_model_status():
    """Get status of all ML models."""
    return model_manager.get_all_status()


@router.post("/train")
def train_models(db: Session = Depends(get_db)):
    """Retrain all ML models on collected telemetry data."""
    telemetry = db.query(Telemetry).order_by(Telemetry.timestamp.desc()).limit(1000).all()

    if len(telemetry) < 20:
        return {"message": "Not enough data to train. Need at least 20 telemetry records.", "trained": False}

    data = np.array([
        [
            t.cpu_usage or 0, t.memory_usage or 0, t.disk_usage or 0,
            t.network_bytes_sent or 0, t.network_bytes_recv or 0,
            t.active_connections or 0, t.process_count or 0,
        ]
        for t in telemetry
    ])

    model_manager.train_all(data)

    return {
        "message": f"Models trained on {len(data)} samples",
        "trained": True,
        "samples": len(data),
    }


@router.post("/predict/{device_id}", response_model=MLPrediction)
def predict_device_risk(device_id: int, db: Session = Depends(get_db)):
    """Run ML prediction for a specific device."""
    latest = (
        db.query(Telemetry)
        .filter(Telemetry.device_id == device_id)
        .order_by(Telemetry.timestamp.desc())
        .first()
    )

    if not latest:
        return MLPrediction(
            device_id=device_id,
            anomaly_score=0.0,
            risk_level="unknown",
            confidence=0.0,
            details={"error": "No telemetry data available"},
        )

    features = np.array([
        latest.cpu_usage or 0, latest.memory_usage or 0, latest.disk_usage or 0,
        latest.network_bytes_sent or 0, latest.network_bytes_recv or 0,
        latest.active_connections or 0, latest.process_count or 0,
    ])

    analysis = model_manager.analyze_device(device_id, features)

    return MLPrediction(
        device_id=device_id,
        anomaly_score=analysis["anomaly"]["score"],
        risk_level=analysis["overall_severity"],
        confidence=analysis["risk"]["confidence"],
        details=analysis,
    )
