"""Anomaly detection using Isolation Forest for network/resource metrics."""

import numpy as np
import joblib
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.config import settings


class AnomalyDetector:
    """Isolation Forest-based anomaly detector for system telemetry."""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = os.path.join(settings.ML_MODEL_DIR, "anomaly_detector.joblib")
        self.scaler_path = os.path.join(settings.ML_MODEL_DIR, "anomaly_scaler.joblib")
        self.feature_names = [
            "cpu_usage", "memory_usage", "disk_usage",
            "network_bytes_sent", "network_bytes_recv",
            "active_connections", "process_count",
        ]
        self._load_model()

    def _load_model(self):
        """Load pre-trained model if available."""
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            self.is_trained = True

    def train(self, data: np.ndarray, contamination: float = 0.1):
        """Train the Isolation Forest model on telemetry data.

        Args:
            data: numpy array of shape (n_samples, n_features)
            contamination: expected proportion of anomalies
        """
        os.makedirs(settings.ML_MODEL_DIR, exist_ok=True)

        self.scaler.fit(data)
        scaled_data = self.scaler.transform(data)

        self.model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(scaled_data)
        self.is_trained = True

        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)

    def predict(self, features: np.ndarray) -> tuple[float, bool]:
        """Predict anomaly score for a single sample.

        Returns:
            (anomaly_score, is_anomaly): score in [0,1] and boolean flag
        """
        if not self.is_trained:
            return 0.0, False

        scaled = self.scaler.transform(features.reshape(1, -1))
        raw_score = self.model.decision_function(scaled)[0]
        prediction = self.model.predict(scaled)[0]

        # Convert to 0-1 scale (lower decision_function = more anomalous)
        anomaly_score = max(0.0, min(1.0, 0.5 - raw_score))

        return float(anomaly_score), prediction == -1

    def batch_predict(self, data: np.ndarray) -> list[dict]:
        """Predict anomaly scores for multiple samples."""
        if not self.is_trained:
            return [{"anomaly_score": 0.0, "is_anomaly": False} for _ in range(len(data))]

        scaled = self.scaler.transform(data)
        raw_scores = self.model.decision_function(scaled)
        predictions = self.model.predict(scaled)

        results = []
        for score, pred in zip(raw_scores, predictions):
            anomaly_score = max(0.0, min(1.0, 0.5 - score))
            results.append({
                "anomaly_score": float(anomaly_score),
                "is_anomaly": pred == -1,
            })
        return results

    def get_status(self) -> dict:
        return {
            "model_name": "IsolationForest_AnomalyDetector",
            "trained": self.is_trained,
            "features": self.feature_names,
        }
