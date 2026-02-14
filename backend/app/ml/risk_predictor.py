"""Risk prediction using Random Forest classifier per ISO 31000."""

import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from app.config import settings


class RiskPredictor:
    """Random Forest classifier for risk level prediction (ISO 31000: likelihood x impact)."""

    RISK_LEVELS = ["low", "medium", "high", "critical"]

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = os.path.join(settings.ML_MODEL_DIR, "risk_predictor.joblib")
        self.scaler_path = os.path.join(settings.ML_MODEL_DIR, "risk_scaler.joblib")
        self.feature_names = [
            "cpu_usage", "memory_usage", "disk_usage",
            "network_bytes_sent", "network_bytes_recv",
            "active_connections", "process_count",
            "anomaly_score",
        ]
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            self.is_trained = True

    def train(self, features: np.ndarray, labels: np.ndarray):
        """Train risk predictor on labeled data.

        Args:
            features: (n_samples, n_features)
            labels: integer labels 0=low, 1=medium, 2=high, 3=critical
        """
        os.makedirs(settings.ML_MODEL_DIR, exist_ok=True)

        self.scaler.fit(features)
        scaled = self.scaler.transform(features)

        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(scaled, labels)
        self.is_trained = True

        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)

    def predict(self, features: np.ndarray) -> dict:
        """Predict risk level for a single sample.

        Returns:
            dict with risk_level, confidence, likelihood, impact, risk_score
        """
        if not self.is_trained:
            return {
                "risk_level": "medium",
                "confidence": 0.0,
                "likelihood": 0.5,
                "impact": 0.5,
                "risk_score": 0.25,
            }

        scaled = self.scaler.transform(features.reshape(1, -1))
        prediction = self.model.predict(scaled)[0]
        probabilities = self.model.predict_proba(scaled)[0]
        confidence = float(np.max(probabilities))

        risk_level = self.RISK_LEVELS[int(prediction)]

        # ISO 31000: derive likelihood and impact from risk level
        likelihood_map = {"low": 0.2, "medium": 0.5, "high": 0.75, "critical": 0.95}
        impact_map = {"low": 0.2, "medium": 0.5, "high": 0.75, "critical": 0.95}

        likelihood = likelihood_map[risk_level]
        impact = impact_map[risk_level]

        return {
            "risk_level": risk_level,
            "confidence": confidence,
            "likelihood": likelihood,
            "impact": impact,
            "risk_score": likelihood * impact,
        }

    def get_status(self) -> dict:
        return {
            "model_name": "RandomForest_RiskPredictor",
            "trained": self.is_trained,
            "risk_levels": self.RISK_LEVELS,
        }
