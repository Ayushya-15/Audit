"""Tests for RiskShield API endpoints and ML modules."""

import pytest
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine, SessionLocal
from app.ml.anomaly_detector import AnomalyDetector
from app.ml.risk_predictor import RiskPredictor
from app.ml.behavior_profiler import BehaviorProfiler


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


# --- API Tests ---

class TestHealthAndRoot:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "RiskShield"

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestDeviceRoutes:
    def test_list_devices_empty(self, client):
        resp = client.get("/api/devices/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_device(self, client):
        resp = client.post("/api/devices/", json={
            "hostname": "test-pc",
            "ip_address": "10.0.0.1",
            "mac_address": "aa:bb:cc:dd:ee:ff",
            "os_type": "Linux",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["hostname"] == "test-pc"
        assert data["ip_address"] == "10.0.0.1"

    def test_create_duplicate_device(self, client):
        client.post("/api/devices/", json={
            "hostname": "test-pc",
            "ip_address": "10.0.0.1",
        })
        resp = client.post("/api/devices/", json={
            "hostname": "test-pc-2",
            "ip_address": "10.0.0.1",
        })
        assert resp.status_code == 400

    def test_discover_devices(self, client):
        resp = client.post("/api/devices/discover?count=3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

    def test_get_device(self, client):
        create_resp = client.post("/api/devices/", json={
            "hostname": "test-pc",
            "ip_address": "10.0.0.99",
        })
        device_id = create_resp.json()["id"]
        resp = client.get(f"/api/devices/{device_id}")
        assert resp.status_code == 200
        assert resp.json()["hostname"] == "test-pc"

    def test_get_nonexistent_device(self, client):
        resp = client.get("/api/devices/9999")
        assert resp.status_code == 404

    def test_delete_device(self, client):
        create_resp = client.post("/api/devices/", json={
            "hostname": "to-delete",
            "ip_address": "10.0.0.100",
        })
        device_id = create_resp.json()["id"]
        resp = client.delete(f"/api/devices/{device_id}")
        assert resp.status_code == 200


class TestRiskRoutes:
    def test_list_risks_empty(self, client):
        resp = client.get("/api/risks/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_dashboard(self, client):
        resp = client.get("/api/risks/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_devices" in data
        assert "total_risks" in data

    def test_heatmap(self, client):
        resp = client.get("/api/risks/heatmap")
        assert resp.status_code == 200

    def test_run_scan(self, client):
        # First discover devices
        client.post("/api/devices/discover?count=3")
        # Run scan
        resp = client.post("/api/risks/scan")
        assert resp.status_code == 200
        data = resp.json()
        assert "telemetry_collected" in data

    def test_alerts(self, client):
        resp = client.get("/api/risks/alerts")
        assert resp.status_code == 200


class TestMLRoutes:
    def test_model_status(self, client):
        resp = client.get("/api/ml/status")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3  # 3 models

    def test_train_insufficient_data(self, client):
        resp = client.post("/api/ml/train")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trained"] is False


class TestTreatmentRoutes:
    def test_audit_log(self, client):
        resp = client.get("/api/treatment/audit-log")
        assert resp.status_code == 200


class TestReportRoutes:
    def test_generate_pdf(self, client):
        resp = client.get("/api/reports/pdf")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"


# --- ML Unit Tests ---

class TestAnomalyDetector:
    def test_untrained_prediction(self):
        detector = AnomalyDetector()
        detector.is_trained = False
        detector.model = None
        score, is_anom = detector.predict(np.array([50, 50, 50, 1000, 1000, 10, 100]))
        assert score == 0.0
        assert is_anom is False

    def test_train_and_predict(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.ML_MODEL_DIR", str(tmp_path))
        detector = AnomalyDetector()
        detector.model_path = str(tmp_path / "ad.joblib")
        detector.scaler_path = str(tmp_path / "as.joblib")

        # Generate normal + anomalous data
        np.random.seed(42)
        normal = np.random.uniform(10, 60, (100, 7))
        anomalous = np.random.uniform(80, 100, (10, 7))
        data = np.vstack([normal, anomalous])

        detector.train(data, contamination=0.1)
        assert detector.is_trained

        # Normal sample should have low anomaly score
        score_normal, _ = detector.predict(np.array([30, 40, 35, 50000, 50000, 20, 100]))
        assert isinstance(score_normal, float)

        # Anomalous sample should have higher anomaly score
        score_anom, _ = detector.predict(np.array([99, 99, 99, 5000000, 5000000, 400, 700]))
        assert isinstance(score_anom, float)


class TestRiskPredictor:
    def test_untrained_prediction(self):
        predictor = RiskPredictor()
        predictor.is_trained = False
        predictor.model = None
        result = predictor.predict(np.array([50, 50, 50, 1000, 1000, 10, 100, 0.3]))
        assert result["risk_level"] == "medium"
        assert result["confidence"] == 0.0

    def test_train_and_predict(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.ML_MODEL_DIR", str(tmp_path))
        predictor = RiskPredictor()
        predictor.model_path = str(tmp_path / "rp.joblib")
        predictor.scaler_path = str(tmp_path / "rs.joblib")

        np.random.seed(42)
        features = np.random.uniform(0, 100, (100, 8))
        labels = np.random.randint(0, 4, 100)

        predictor.train(features, labels)
        assert predictor.is_trained

        result = predictor.predict(np.array([50, 50, 50, 1000, 1000, 10, 100, 0.5]))
        assert result["risk_level"] in ["low", "medium", "high", "critical"]
        assert 0 <= result["confidence"] <= 1


class TestBehaviorProfiler:
    def test_no_profile_deviation(self):
        profiler = BehaviorProfiler()
        profiler.profiles = {}
        result = profiler.detect_deviation(999, np.array([50, 50, 50, 1000, 1000, 10, 100]))
        assert result["is_deviation"] is False

    def test_profile_update_and_deviation(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.ML_MODEL_DIR", str(tmp_path))
        profiler = BehaviorProfiler()
        profiler.model_path = str(tmp_path / "bp.joblib")

        # Build a profile with normal data
        np.random.seed(42)
        for _ in range(25):
            normal = np.random.uniform(20, 50, 7)
            profiler.update_profile(1, normal)

        # Test normal behavior
        result_normal = profiler.detect_deviation(1, np.array([35, 35, 35, 35, 35, 35, 35]))
        assert isinstance(result_normal["deviation_score"], float)

        # Test anomalous behavior
        result_anom = profiler.detect_deviation(1, np.array([999, 999, 999, 999, 999, 999, 999]))
        assert result_anom["deviation_score"] > result_normal["deviation_score"]
