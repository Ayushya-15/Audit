"""API routes for device management and network discovery."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Device
from app.models.schemas import DeviceCreate, DeviceResponse
from app.network.discovery import discover_devices_simulated

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("/", response_model=list[DeviceResponse])
def list_devices(db: Session = Depends(get_db)):
    """List all discovered devices."""
    return db.query(Device).all()


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: int, db: Session = Depends(get_db)):
    """Get a specific device by ID."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post("/", response_model=DeviceResponse)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """Manually register a device."""
    existing = db.query(Device).filter(Device.ip_address == device.ip_address).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device with this IP already exists")

    db_device = Device(**device.model_dump())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@router.post("/discover", response_model=list[DeviceResponse])
def discover_devices(count: int = 5, db: Session = Depends(get_db)):
    """Trigger network discovery to find devices."""
    devices = discover_devices_simulated(db, count=count)
    return devices


@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    """Remove a device from monitoring."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    db.delete(device)
    db.commit()
    return {"message": f"Device {device_id} deleted"}
