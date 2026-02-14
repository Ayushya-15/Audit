"""API routes for report generation."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.reports.generator import generate_risk_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/pdf")
def download_risk_report(db: Session = Depends(get_db)):
    """Generate and download a PDF risk assessment report."""
    pdf_bytes = generate_risk_report(db)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=riskshield_report.pdf"},
    )
