"""ISO 31000 Risk Assessment module."""

import datetime
import numpy as np
from sqlalchemy.orm import Session

from app.models.db_models import Device, Telemetry, Risk, Alert, AuditLog
from app.ml.model_manager import model_manager


def assess_device_risk(db: Session, device: Device) -> list[Risk]:
    """Perform ISO 31000 risk assessment on a device using ML analysis.

    ISO 31000 phases: Context Establishment → Risk Identification →
    Risk Analysis → Risk Evaluation → Risk Treatment
    """
    # Get latest telemetry
    latest = (
        db.query(Telemetry)
        .filter(Telemetry.device_id == device.id)
        .order_by(Telemetry.timestamp.desc())
        .first()
    )

    if not latest:
        return []

    features = np.array([
        latest.cpu_usage or 0,
        latest.memory_usage or 0,
        latest.disk_usage or 0,
        latest.network_bytes_sent or 0,
        latest.network_bytes_recv or 0,
        latest.active_connections or 0,
        latest.process_count or 0,
    ])

    # ML analysis
    analysis = model_manager.analyze_device(device.id, features)
    risks = []

    # Log audit entry - Context Establishment
    _log_audit(db, "risk_assessment_start", f"Assessing device {device.hostname}", "context_establishment")

    # Risk Identification based on ML results
    if analysis["anomaly"]["is_anomaly"]:
        risk = _create_risk(
            db, device, analysis,
            risk_type="behavioral_anomaly",
            title=f"Behavioral Anomaly on {device.hostname}",
            description=f"ML anomaly detector flagged unusual patterns. "
                        f"Anomaly score: {analysis['anomaly']['score']:.2f}",
        )
        risks.append(risk)

    if analysis["behavior"]["is_deviation"]:
        deviant = analysis["behavior"].get("deviant_features", [])
        desc = ", ".join([f"{d['feature']} (z={d['z_score']:.1f})" for d in deviant])
        risk = _create_risk(
            db, device, analysis,
            risk_type="behavior_deviation",
            title=f"Behavior Deviation on {device.hostname}",
            description=f"Deviant features: {desc}" if desc else "General behavior deviation detected",
        )
        risks.append(risk)

    # Resource exhaustion risk
    if (latest.cpu_usage or 0) > 90 or (latest.memory_usage or 0) > 90:
        risk = _create_risk(
            db, device, analysis,
            risk_type="resource_exhaustion",
            title=f"Resource Exhaustion on {device.hostname}",
            description=f"CPU: {latest.cpu_usage}%, Memory: {latest.memory_usage}%",
        )
        risks.append(risk)

    # Suspicious network activity
    if (latest.active_connections or 0) > 100:
        risk = _create_risk(
            db, device, analysis,
            risk_type="suspicious_network",
            title=f"Suspicious Network Activity on {device.hostname}",
            description=f"Active connections: {latest.active_connections}, "
                        f"Traffic: {latest.network_bytes_sent}B sent, {latest.network_bytes_recv}B recv",
        )
        risks.append(risk)

    # Log audit - Risk Evaluation complete
    _log_audit(db, "risk_assessment_complete",
               f"Found {len(risks)} risks for {device.hostname}",
               "risk_evaluation")

    return risks


def _create_risk(db: Session, device: Device, analysis: dict,
                 risk_type: str, title: str, description: str) -> Risk:
    """Create a risk entry with ML-derived scores."""
    severity = analysis["overall_severity"]
    likelihood = analysis["risk"]["likelihood"]
    impact = analysis["risk"]["impact"]
    risk_score = likelihood * impact
    confidence = analysis["risk"]["confidence"]

    # Generate treatment recommendation
    treatment = _generate_treatment(risk_type, severity, device.hostname)

    risk = Risk(
        device_id=device.id,
        risk_type=risk_type,
        title=title,
        description=description,
        severity=severity,
        likelihood=round(likelihood, 3),
        impact=round(impact, 3),
        risk_score=round(risk_score, 3),
        ml_confidence=round(confidence, 3),
        status="open",
        treatment_plan=treatment,
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)

    # Create alert for high/critical risks
    if severity in ("high", "critical"):
        alert = Alert(
            risk_id=risk.id,
            title=f"[{severity.upper()}] {title}",
            message=description,
            severity=severity,
        )
        db.add(alert)
        db.commit()

    return risk


def _generate_treatment(risk_type: str, severity: str, hostname: str) -> str:
    """Generate ISO 31000-aligned treatment recommendation."""
    treatments = {
        "behavioral_anomaly": (
            f"1. Isolate {hostname} from network (probability 85% effective)\n"
            f"2. Run deep behavioral analysis scan\n"
            f"3. Review recent user activity logs\n"
            f"4. Re-baseline behavior profile after investigation"
        ),
        "behavior_deviation": (
            f"1. Monitor {hostname} closely for 24 hours\n"
            f"2. Compare with peer device profiles\n"
            f"3. Interview device user for context\n"
            f"4. Update behavior baseline if activity is legitimate"
        ),
        "resource_exhaustion": (
            f"1. Identify resource-intensive processes on {hostname}\n"
            f"2. Check for cryptocurrency mining or malware\n"
            f"3. Apply resource limits/quotas\n"
            f"4. Schedule maintenance window for investigation"
        ),
        "suspicious_network": (
            f"1. Apply firewall rules to restrict {hostname} traffic\n"
            f"2. Capture and analyze network traffic\n"
            f"3. Check for data exfiltration indicators\n"
            f"4. Block suspicious outbound connections"
        ),
    }
    return treatments.get(risk_type, f"Investigate and remediate {risk_type} on {hostname}")


def _log_audit(db: Session, action: str, details: str, iso_phase: str):
    entry = AuditLog(action=action, details=details, iso_phase=iso_phase)
    db.add(entry)
    db.commit()
