"""Telemetry collection module for gathering system metrics."""

import datetime
import random
import numpy as np
from sqlalchemy.orm import Session

from app.models.db_models import Device, Telemetry
from app.ml.model_manager import model_manager


def collect_telemetry_simulated(db: Session, device: Device) -> Telemetry:
    """Simulate telemetry collection from a device.

    In production, this would use SSH/WMI/SNMP to gather real metrics.
    """
    # Generate realistic-looking telemetry with occasional anomalies
    is_anomalous = random.random() < 0.15  # 15% chance of anomaly

    if is_anomalous:
        cpu = random.uniform(85, 100)
        memory = random.uniform(80, 99)
        disk = random.uniform(75, 98)
        net_sent = random.uniform(500_000, 5_000_000)
        net_recv = random.uniform(500_000, 10_000_000)
        connections = random.randint(50, 500)
        processes = random.randint(200, 800)
    else:
        cpu = random.uniform(5, 60)
        memory = random.uniform(20, 70)
        disk = random.uniform(20, 60)
        net_sent = random.uniform(1000, 100_000)
        net_recv = random.uniform(1000, 200_000)
        connections = random.randint(5, 50)
        processes = random.randint(50, 200)

    # Run ML analysis
    features = np.array([cpu, memory, disk, net_sent, net_recv, connections, processes])
    analysis = model_manager.analyze_device(device.id, features)
    anomaly_score = analysis["anomaly"]["score"]

    telemetry = Telemetry(
        device_id=device.id,
        timestamp=datetime.datetime.utcnow(),
        cpu_usage=round(cpu, 2),
        memory_usage=round(memory, 2),
        disk_usage=round(disk, 2),
        network_bytes_sent=round(net_sent, 2),
        network_bytes_recv=round(net_recv, 2),
        active_connections=connections,
        process_count=processes,
        anomaly_score=round(anomaly_score, 4),
    )
    db.add(telemetry)
    db.commit()
    db.refresh(telemetry)

    return telemetry


def collect_all_telemetry(db: Session) -> list[Telemetry]:
    """Collect telemetry from all active devices."""
    devices = db.query(Device).filter(Device.status == "active").all()
    results = []
    for device in devices:
        t = collect_telemetry_simulated(db, device)
        results.append(t)
    return results
