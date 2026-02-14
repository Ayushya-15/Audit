"""API routes for risk treatment actions."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import TreatmentAction, TreatmentResult
from app.risk.treatment import execute_treatment
from app.models.db_models import AuditLog
from app.models.schemas import AuditLogResponse

router = APIRouter(prefix="/api/treatment", tags=["treatment"])


@router.post("/execute", response_model=TreatmentResult)
def execute_treatment_action(action: TreatmentAction, db: Session = Depends(get_db)):
    """Execute a risk treatment action (quarantine, firewall_rule, patch, accept, escalate)."""
    result = execute_treatment(db, action.risk_id, action.action, action.parameters)
    return TreatmentResult(**result)


@router.get("/audit-log", response_model=list[AuditLogResponse])
def get_audit_log(limit: int = 100, db: Session = Depends(get_db)):
    """Get ISO 31000 compliance audit trail."""
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
