"""Network discovery module for detecting end-user devices."""

import datetime
import random
from sqlalchemy.orm import Session

from app.models.db_models import Device


def discover_devices_simulated(db: Session, count: int = 5) -> list[Device]:
    """Simulate network discovery of end-user devices.

    In production, this would use SNMP, ARP scanning, or agentless WMI/SSH.
    For demo purposes, generates simulated devices.
    """
    os_types = ["Windows 11", "Ubuntu 22.04", "macOS Ventura", "Windows 10", "CentOS 8"]
    hostnames = ["workstation-01", "dev-server-02", "finance-pc-03", "hr-laptop-04", "db-server-05"]
    base_ip = "192.168.1."

    devices = []
    for i in range(count):
        ip = f"{base_ip}{10 + i}"

        existing = db.query(Device).filter(Device.ip_address == ip).first()
        if existing:
            existing.last_seen = datetime.datetime.utcnow()
            existing.status = "active"
            devices.append(existing)
            continue

        mac = ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])
        device = Device(
            hostname=hostnames[i % len(hostnames)],
            ip_address=ip,
            mac_address=mac,
            os_type=os_types[i % len(os_types)],
            status="active",
        )
        db.add(device)
        devices.append(device)

    db.commit()
    for d in devices:
        db.refresh(d)
    return devices
