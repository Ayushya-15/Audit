"""API routes for risk management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Device, Risk, Alert
from app.models.schemas import RiskResponse, AlertResponse, DashboardStats, RiskHeatmapData
from app.risk.assessment import assess_device_risk
from app.network.telemetry import collect_all_telemetry

router = APIRouter(prefix="/api/risks", tags=["risks"])


@router.get("/", response_model=list[RiskResponse])
def list_risks(
    status: str | None = None,
    severity: str | None = None,
    device_id: int | None = None,
    db: Session = Depends(get_db),
):
    """List all risks with optional filters."""
    query = db.query(Risk)
    if status:
        query = query.filter(Risk.status == status)
    if severity:
        query = query.filter(Risk.severity == severity)
    if device_id:
        query = query.filter(Risk.device_id == device_id)
    return query.order_by(Risk.risk_score.desc()).all()


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    devices = db.query(Device).all()
    risks = db.query(Risk).all()
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(10).all()

    total_risks = len(risks)
    return DashboardStats(
        total_devices=len(devices),
        active_devices=len([d for d in devices if d.status == "active"]),
        quarantined_devices=len([d for d in devices if d.status == "quarantined"]),
        total_risks=total_risks,
        open_risks=len([r for r in risks if r.status == "open"]),
        critical_risks=len([r for r in risks if r.severity == "critical"]),
        high_risks=len([r for r in risks if r.severity == "high"]),
        medium_risks=len([r for r in risks if r.severity == "medium"]),
        low_risks=len([r for r in risks if r.severity == "low"]),
        avg_risk_score=round(sum(r.risk_score for r in risks) / max(total_risks, 1), 3),
        recent_alerts=alerts,
    )


@router.get("/heatmap", response_model=list[RiskHeatmapData])
def get_risk_heatmap(db: Session = Depends(get_db)):
    """Get risk heatmap data for all devices."""
    devices = db.query(Device).all()
    result = []
    for device in devices:
        device_risks = db.query(Risk).filter(Risk.device_id == device.id).all()
        if device_risks:
            max_risk = max(device_risks, key=lambda r: r.risk_score)
            result.append(RiskHeatmapData(
                device_id=device.id,
                hostname=device.hostname,
                ip_address=device.ip_address,
                risk_score=max_risk.risk_score,
                severity=max_risk.severity,
                risk_count=len(device_risks),
            ))
        else:
            result.append(RiskHeatmapData(
                device_id=device.id,
                hostname=device.hostname,
                ip_address=device.ip_address,
                risk_score=0.0,
                severity="low",
                risk_count=0,
            ))
    return result


@router.post("/scan")
def run_scan(db: Session = Depends(get_db)):
    """Run a full network scan: collect telemetry and assess risks."""
    # Collect telemetry from all devices
    telemetry = collect_all_telemetry(db)

    # Assess risks for each device
    all_risks = []
    devices = db.query(Device).filter(Device.status == "active").all()
    for device in devices:
        risks = assess_device_risk(db, device)
        all_risks.extend(risks)

    return {
        "telemetry_collected": len(telemetry),
        "risks_identified": len(all_risks),
        "message": "Scan complete",
    }


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(
    acknowledged: bool | None = None,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """List alerts."""
    query = db.query(Alert)
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == acknowledged)
    return query.order_by(Alert.created_at.desc()).limit(limit).all()


@router.put("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Acknowledge an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    db.commit()
    return {"message": f"Alert {alert_id} acknowledged"}
