"""PDF report generation using ReportLab."""

import io
import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)
from sqlalchemy.orm import Session

from app.models.db_models import Device, Risk, AuditLog


def generate_risk_report(db: Session) -> bytes:
    """Generate a comprehensive PDF risk report aligned with ISO 31000."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("CustomTitle", parent=styles["Title"], fontSize=24, spaceAfter=20)
    heading_style = ParagraphStyle("CustomHeading", parent=styles["Heading1"], fontSize=16, spaceAfter=12)
    subheading_style = ParagraphStyle("CustomSub", parent=styles["Heading2"], fontSize=13, spaceAfter=8)

    elements = []

    # --- Title Page ---
    elements.append(Spacer(1, 2 * inch))
    elements.append(Paragraph("RiskShield", title_style))
    elements.append(Paragraph("GRC Compliance Risk Assessment Report", styles["Heading2"]))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(f"Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    elements.append(Paragraph("Standard: ISO 31000 Risk Management", styles["Normal"]))
    elements.append(PageBreak())

    # --- Executive Summary ---
    elements.append(Paragraph("1. Executive Summary", heading_style))

    devices = db.query(Device).all()
    risks = db.query(Risk).all()

    total_devices = len(devices)
    total_risks = len(risks)
    open_risks = len([r for r in risks if r.status == "open"])
    critical = len([r for r in risks if r.severity == "critical"])
    high = len([r for r in risks if r.severity == "high"])
    medium = len([r for r in risks if r.severity == "medium"])
    low = len([r for r in risks if r.severity == "low"])
    avg_score = sum(r.risk_score for r in risks) / max(len(risks), 1)

    summary_data = [
        ["Metric", "Value"],
        ["Total Devices Scanned", str(total_devices)],
        ["Total Risks Identified", str(total_risks)],
        ["Open Risks", str(open_risks)],
        ["Critical Risks", str(critical)],
        ["High Risks", str(high)],
        ["Medium Risks", str(medium)],
        ["Low Risks", str(low)],
        ["Average Risk Score", f"{avg_score:.3f}"],
    ]

    table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))

    # --- Detailed Findings ---
    elements.append(Paragraph("2. Detailed Findings", heading_style))

    for device in devices:
        device_risks = [r for r in risks if r.device_id == device.id]
        if not device_risks:
            continue

        elements.append(Paragraph(f"{device.hostname} ({device.ip_address})", subheading_style))

        risk_data = [["Risk", "Severity", "Score", "Confidence", "Status"]]
        for r in device_risks:
            risk_data.append([
                r.title[:40],
                r.severity.upper(),
                f"{r.risk_score:.3f}",
                f"{(r.ml_confidence or 0):.1%}",
                r.status,
            ])

        if len(risk_data) > 1:
            t = Table(risk_data, colWidths=[2.2 * inch, 1 * inch, 0.8 * inch, 1 * inch, 0.8 * inch])
            severity_colors = {
                "CRITICAL": colors.HexColor("#dc2626"),
                "HIGH": colors.HexColor("#ea580c"),
                "MEDIUM": colors.HexColor("#ca8a04"),
                "LOW": colors.HexColor("#16a34a"),
            }
            style_cmds = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
            ]
            for row_idx, r in enumerate(device_risks, start=1):
                sev_color = severity_colors.get(r.severity.upper(), colors.grey)
                style_cmds.append(("TEXTCOLOR", (1, row_idx), (1, row_idx), sev_color))

            t.setStyle(TableStyle(style_cmds))
            elements.append(t)
            elements.append(Spacer(1, 0.2 * inch))

    elements.append(PageBreak())

    # --- Treatment Plans ---
    elements.append(Paragraph("3. Treatment Plans", heading_style))
    for r in risks:
        if r.treatment_plan:
            elements.append(Paragraph(f"Risk #{r.id}: {r.title}", subheading_style))
            elements.append(Paragraph(f"Severity: {r.severity.upper()} | Score: {r.risk_score:.3f}", styles["Normal"]))
            for line in r.treatment_plan.split("\n"):
                elements.append(Paragraph(line, styles["Normal"]))
            elements.append(Spacer(1, 0.15 * inch))

    elements.append(PageBreak())

    # --- Compliance Audit Trail ---
    elements.append(Paragraph("4. ISO 31000 Compliance Audit Trail", heading_style))

    audit_entries = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(50).all()
    if audit_entries:
        audit_data = [["Timestamp", "Action", "ISO Phase", "Details"]]
        for entry in audit_entries:
            audit_data.append([
                entry.timestamp.strftime("%Y-%m-%d %H:%M"),
                entry.action,
                entry.iso_phase or "N/A",
                (entry.details or "")[:50],
            ])

        at = Table(audit_data, colWidths=[1.5 * inch, 1.5 * inch, 1.3 * inch, 2 * inch])
        at.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ]))
        elements.append(at)
    else:
        elements.append(Paragraph("No audit entries recorded.", styles["Normal"]))

    doc.build(elements)
    return buffer.getvalue()
