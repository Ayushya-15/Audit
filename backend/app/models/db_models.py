"""SQLAlchemy database models for RiskShield."""

import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(255), nullable=False)
    ip_address = Column(String(45), unique=True, nullable=False)
    mac_address = Column(String(17), nullable=True)
    os_type = Column(String(100), nullable=True)
    status = Column(String(20), default="active")  # active, quarantined, offline
    discovered_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)

    telemetry = relationship("Telemetry", back_populates="device", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="device", cascade="all, delete-orphan")


class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    disk_usage = Column(Float, nullable=True)
    network_bytes_sent = Column(Float, nullable=True)
    network_bytes_recv = Column(Float, nullable=True)
    active_connections = Column(Integer, nullable=True)
    process_count = Column(Integer, nullable=True)
    anomaly_score = Column(Float, nullable=True)

    device = relationship("Device", back_populates="telemetry")


class Risk(Base):
    __tablename__ = "risks"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    risk_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    likelihood = Column(Float, nullable=False)  # 0.0 - 1.0, ISO 31000
    impact = Column(Float, nullable=False)       # 0.0 - 1.0, ISO 31000
    risk_score = Column(Float, nullable=False)   # likelihood * impact
    ml_confidence = Column(Float, nullable=True)
    status = Column(String(20), default="open")  # open, mitigated, accepted, closed
    treatment_plan = Column(Text, nullable=True)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    device = relationship("Device", back_populates="risks")
    alerts = relationship("Alert", back_populates="risk", cascade="all, delete-orphan")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    risk_id = Column(Integer, ForeignKey("risks.id"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    risk = relationship("Risk", back_populates="alerts")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    user = Column(String(100), default="system")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    iso_phase = Column(String(50), nullable=True)  # ISO 31000 phase
