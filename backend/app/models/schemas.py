"""Pydantic schemas for API request/response models."""

import datetime
from pydantic import BaseModel, Field


# --- Device Schemas ---

class DeviceBase(BaseModel):
    hostname: str
    ip_address: str
    mac_address: str | None = None
    os_type: str | None = None


class DeviceCreate(DeviceBase):
    pass


class DeviceResponse(DeviceBase):
    id: int
    status: str
    discovered_at: datetime.datetime
    last_seen: datetime.datetime

    class Config:
        from_attributes = True


# --- Telemetry Schemas ---

class TelemetryBase(BaseModel):
    cpu_usage: float | None = None
    memory_usage: float | None = None
    disk_usage: float | None = None
    network_bytes_sent: float | None = None
    network_bytes_recv: float | None = None
    active_connections: int | None = None
    process_count: int | None = None


class TelemetryCreate(TelemetryBase):
    device_id: int


class TelemetryResponse(TelemetryBase):
    id: int
    device_id: int
    timestamp: datetime.datetime
    anomaly_score: float | None = None

    class Config:
        from_attributes = True


# --- Risk Schemas ---

class RiskBase(BaseModel):
    risk_type: str
    title: str
    description: str | None = None
    severity: str
    likelihood: float = Field(ge=0.0, le=1.0)
    impact: float = Field(ge=0.0, le=1.0)


class RiskCreate(RiskBase):
    device_id: int


class RiskResponse(RiskBase):
    id: int
    device_id: int
    risk_score: float
    ml_confidence: float | None = None
    status: str
    treatment_plan: str | None = None
    detected_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


# --- Alert Schemas ---

class AlertResponse(BaseModel):
    id: int
    risk_id: int | None = None
    title: str
    message: str
    severity: str
    acknowledged: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# --- Treatment Schemas ---

class TreatmentAction(BaseModel):
    risk_id: int
    action: str  # quarantine, firewall_rule, patch, accept, escalate
    parameters: dict | None = None


class TreatmentResult(BaseModel):
    risk_id: int
    action: str
    success: bool
    message: str
    new_risk_score: float | None = None


# --- Dashboard Schemas ---

class DashboardStats(BaseModel):
    total_devices: int
    active_devices: int
    quarantined_devices: int
    total_risks: int
    open_risks: int
    critical_risks: int
    high_risks: int
    medium_risks: int
    low_risks: int
    avg_risk_score: float
    recent_alerts: list[AlertResponse]


class RiskHeatmapData(BaseModel):
    device_id: int
    hostname: str
    ip_address: str
    risk_score: float
    severity: str
    risk_count: int


# --- ML Schemas ---

class MLModelStatus(BaseModel):
    model_name: str
    trained: bool
    last_trained: datetime.datetime | None = None
    accuracy: float | None = None
    samples_count: int


class MLPrediction(BaseModel):
    device_id: int
    anomaly_score: float
    risk_level: str
    confidence: float
    details: dict


# --- Audit Log Schemas ---

class AuditLogResponse(BaseModel):
    id: int
    action: str
    details: str | None = None
    user: str
    timestamp: datetime.datetime
    iso_phase: str | None = None

    class Config:
        from_attributes = True
