"""ML model manager - centralizes all ML model operations."""

import numpy as np
import datetime

from app.ml.anomaly_detector import AnomalyDetector
from app.ml.risk_predictor import RiskPredictor
from app.ml.behavior_profiler import BehaviorProfiler


class ModelManager:
    """Manages all ML models for RiskShield."""

    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.risk_predictor = RiskPredictor()
        self.behavior_profiler = BehaviorProfiler()
        self.last_trained: datetime.datetime | None = None
        self.training_samples = 0

    def train_all(self, telemetry_data: np.ndarray, risk_labels: np.ndarray | None = None):
        """Train all models with provided data.

        Args:
            telemetry_data: (n_samples, 7) - cpu, mem, disk, net_sent, net_recv, conns, procs
            risk_labels: optional (n_samples,) - 0=low, 1=med, 2=high, 3=critical
        """
        # Train anomaly detector
        self.anomaly_detector.train(telemetry_data, contamination=0.1)

        # Generate anomaly scores for risk predictor features
        anomaly_results = self.anomaly_detector.batch_predict(telemetry_data)
        anomaly_scores = np.array([r["anomaly_score"] for r in anomaly_results]).reshape(-1, 1)

        # Combine features for risk predictor
        risk_features = np.hstack([telemetry_data, anomaly_scores])

        if risk_labels is None:
            # Auto-generate labels based on anomaly scores + heuristics
            risk_labels = self._auto_label(telemetry_data, anomaly_scores.flatten())

        self.risk_predictor.train(risk_features, risk_labels)

        self.last_trained = datetime.datetime.utcnow()
        self.training_samples = len(telemetry_data)

    def analyze_device(self, device_id: int, features: np.ndarray) -> dict:
        """Run full ML analysis on a device's telemetry.

        Args:
            device_id: device identifier
            features: 1D array of 7 telemetry features

        Returns:
            Combined analysis results
        """
        # Anomaly detection
        anomaly_score, is_anomaly = self.anomaly_detector.predict(features)

        # Risk prediction
        risk_features = np.append(features, anomaly_score)
        risk_result = self.risk_predictor.predict(risk_features)

        # Behavior profiling
        self.behavior_profiler.update_profile(device_id, features)
        behavior_result = self.behavior_profiler.detect_deviation(device_id, features)

        # Combined risk assessment
        combined_score = (
            anomaly_score * 0.3
            + risk_result["risk_score"] * 0.4
            + behavior_result["deviation_score"] * 0.3
        )

        return {
            "device_id": device_id,
            "anomaly": {
                "score": anomaly_score,
                "is_anomaly": is_anomaly,
            },
            "risk": risk_result,
            "behavior": behavior_result,
            "combined_risk_score": combined_score,
            "overall_severity": self._score_to_severity(combined_score),
        }

    @staticmethod
    def _score_to_severity(score: float) -> str:
        if score >= 0.75:
            return "critical"
        elif score >= 0.5:
            return "high"
        elif score >= 0.25:
            return "medium"
        return "low"

    @staticmethod
    def _auto_label(data: np.ndarray, anomaly_scores: np.ndarray) -> np.ndarray:
        """Generate risk labels based on heuristics."""
        labels = np.zeros(len(data), dtype=int)
        for i in range(len(data)):
            cpu, mem = data[i, 0], data[i, 1]
            anom = anomaly_scores[i]

            score = anom * 0.4 + (cpu / 100.0) * 0.3 + (mem / 100.0) * 0.3
            if score >= 0.75:
                labels[i] = 3  # critical
            elif score >= 0.5:
                labels[i] = 2  # high
            elif score >= 0.25:
                labels[i] = 1  # medium
            else:
                labels[i] = 0  # low
        return labels

    def get_all_status(self) -> list[dict]:
        return [
            {
                **self.anomaly_detector.get_status(),
                "last_trained": self.last_trained.isoformat() if self.last_trained else None,
                "samples_count": self.training_samples,
            },
            {
                **self.risk_predictor.get_status(),
                "last_trained": self.last_trained.isoformat() if self.last_trained else None,
                "samples_count": self.training_samples,
            },
            {
                **self.behavior_profiler.get_status(),
                "last_trained": self.last_trained.isoformat() if self.last_trained else None,
                "samples_count": self.training_samples,
            },
        ]


# Singleton instance
model_manager = ModelManager()
