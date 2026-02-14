"""Risk treatment and remediation actions."""

import datetime
from sqlalchemy.orm import Session

from app.models.db_models import Device, Risk, AuditLog, Alert
from app.ml.model_manager import model_manager


def execute_treatment(db: Session, risk_id: int, action: str, parameters: dict | None = None) -> dict:
    """Execute a risk treatment action per ISO 31000 treatment phase.

    Actions: quarantine, firewall_rule, patch, accept, escalate
    """
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if not risk:
        return {"success": False, "message": "Risk not found"}

    device = db.query(Device).filter(Device.id == risk.device_id).first()
    if not device:
        return {"success": False, "message": "Device not found"}

    result = {"risk_id": risk_id, "action": action, "success": False, "message": ""}

    if action == "quarantine":
        result = _quarantine_device(db, device, risk)
    elif action == "firewall_rule":
        result = _apply_firewall_rule(db, device, risk, parameters)
    elif action == "accept":
        result = _accept_risk(db, risk)
    elif action == "escalate":
        result = _escalate_risk(db, risk)
    elif action == "patch":
        result = _simulate_patch(db, device, risk)
    else:
        result["message"] = f"Unknown action: {action}"
        return result

    # Log treatment action
    _log_audit(db, f"treatment_{action}",
               f"Applied {action} to risk #{risk_id} on {device.hostname}",
               "risk_treatment")

    return result


def _quarantine_device(db: Session, device: Device, risk: Risk) -> dict:
    """Quarantine a device by changing its status."""
    device.status = "quarantined"
    risk.status = "mitigated"
    risk.updated_at = datetime.datetime.utcnow()
    db.commit()

    # Create alert
    alert = Alert(
        risk_id=risk.id,
        title=f"Device {device.hostname} Quarantined",
        message=f"Device quarantined due to risk: {risk.title}",
        severity="high",
    )
    db.add(alert)
    db.commit()

    return {
        "risk_id": risk.id,
        "action": "quarantine",
        "success": True,
        "message": f"Device {device.hostname} ({device.ip_address}) quarantined successfully",
        "new_risk_score": risk.risk_score * 0.2,
    }


def _apply_firewall_rule(db: Session, device: Device, risk: Risk,
                         parameters: dict | None = None) -> dict:
    """Simulate applying a firewall rule."""
    rule = parameters.get("rule", "BLOCK_OUTBOUND") if parameters else "BLOCK_OUTBOUND"

    risk.status = "mitigated"
    risk.updated_at = datetime.datetime.utcnow()
    risk.treatment_plan = f"Firewall rule {rule} applied to {device.ip_address}"
    db.commit()

    return {
        "risk_id": risk.id,
        "action": "firewall_rule",
        "success": True,
        "message": f"Firewall rule '{rule}' applied to {device.ip_address}",
        "new_risk_score": risk.risk_score * 0.3,
    }


def _accept_risk(db: Session, risk: Risk) -> dict:
    """Accept the risk (ISO 31000: risk acceptance)."""
    risk.status = "accepted"
    risk.updated_at = datetime.datetime.utcnow()
    db.commit()

    return {
        "risk_id": risk.id,
        "action": "accept",
        "success": True,
        "message": f"Risk #{risk.id} accepted per ISO 31000 risk acceptance criteria",
        "new_risk_score": risk.risk_score,
    }


def _escalate_risk(db: Session, risk: Risk) -> dict:
    """Escalate the risk for further review."""
    risk.status = "open"
    risk.updated_at = datetime.datetime.utcnow()
    db.commit()

    alert = Alert(
        risk_id=risk.id,
        title=f"Risk Escalated: {risk.title}",
        message=f"Risk #{risk.id} escalated for management review",
        severity=risk.severity,
    )
    db.add(alert)
    db.commit()

    return {
        "risk_id": risk.id,
        "action": "escalate",
        "success": True,
        "message": f"Risk #{risk.id} escalated for management review",
        "new_risk_score": risk.risk_score,
    }


def _simulate_patch(db: Session, device: Device, risk: Risk) -> dict:
    """Simulate applying a patch/fix."""
    risk.status = "mitigated"
    risk.updated_at = datetime.datetime.utcnow()
    db.commit()

    return {
        "risk_id": risk.id,
        "action": "patch",
        "success": True,
        "message": f"Patch applied to {device.hostname}",
        "new_risk_score": risk.risk_score * 0.1,
    }


def _log_audit(db: Session, action: str, details: str, iso_phase: str):
    entry = AuditLog(action=action, details=details, iso_phase=iso_phase)
    db.add(entry)
    db.commit()
