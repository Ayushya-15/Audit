"""Generate synthetic demo data for RiskShield.

Simulates 5 end-user systems with telemetry data and trains ML models.
Run from the backend directory: python -m demo.generate_data
"""

import sys
import os
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import init_db, SessionLocal
from app.network.discovery import discover_devices_simulated
from app.network.telemetry import collect_all_telemetry
from app.risk.assessment import assess_device_risk
from app.ml.model_manager import model_manager


def main():
    print("=" * 60)
    print("  RiskShield - Demo Data Generator")
    print("  Simulating 5 end-user systems")
    print("=" * 60)

    # Initialize database
    print("\n[1/5] Initializing database...")
    init_db()
    db = SessionLocal()

    # Discover devices
    print("[2/5] Discovering 5 network devices...")
    devices = discover_devices_simulated(db, count=5)
    for d in devices:
        print(f"  ✓ {d.hostname} ({d.ip_address}) - {d.os_type}")

    # Generate training data
    print("[3/5] Generating training telemetry (200 samples)...")
    np.random.seed(42)
    normal_data = np.column_stack([
        np.random.uniform(10, 60, 170),   # cpu
        np.random.uniform(20, 70, 170),   # memory
        np.random.uniform(20, 60, 170),   # disk
        np.random.uniform(1000, 100000, 170),   # net_sent
        np.random.uniform(1000, 200000, 170),   # net_recv
        np.random.randint(5, 50, 170),    # connections
        np.random.randint(50, 200, 170),  # processes
    ])
    anomalous_data = np.column_stack([
        np.random.uniform(85, 100, 30),
        np.random.uniform(80, 99, 30),
        np.random.uniform(75, 98, 30),
        np.random.uniform(500000, 5000000, 30),
        np.random.uniform(500000, 10000000, 30),
        np.random.randint(100, 500, 30),
        np.random.randint(200, 800, 30),
    ])
    training_data = np.vstack([normal_data, anomalous_data])
    print(f"  ✓ Generated {len(training_data)} training samples")

    # Train ML models
    print("[4/5] Training ML models...")
    model_manager.train_all(training_data)
    print("  ✓ Anomaly Detector (Isolation Forest) trained")
    print("  ✓ Risk Predictor (Random Forest) trained")
    print("  ✓ Behavior Profiler initialized")

    # Collect telemetry and assess risks
    print("[5/5] Running risk assessment scan...")
    for _ in range(3):  # Multiple rounds to build behavior profiles
        telemetry = collect_all_telemetry(db)

    for device in devices:
        risks = assess_device_risk(db, device)
        if risks:
            print(f"  ⚠ {device.hostname}: {len(risks)} risks detected")
            for r in risks:
                print(f"    - [{r.severity.upper()}] {r.title} (score: {r.risk_score:.3f})")

    db.close()

    print("\n" + "=" * 60)
    print("  Demo data generated successfully!")
    print("  Start the server with: cd backend && uvicorn app.main:app --reload")
    print("  Then open: http://localhost:5173")
    print("=" * 60)


if __name__ == "__main__":
    main()
