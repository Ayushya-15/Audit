"""Behavior profiling using simplified LSTM-like approach for time-series anomalies."""

import numpy as np
import joblib
import os
from sklearn.preprocessing import StandardScaler

from app.config import settings


class BehaviorProfiler:
    """Time-series behavior profiler for detecting deviations in user/system patterns.

    Uses a sliding-window statistical approach as a lightweight alternative
    to full LSTM, suitable for edge deployment. Tracks moving averages and
    standard deviations to detect behavioral deviations.
    """

    def __init__(self):
        self.profiles: dict[int, dict] = {}  # device_id -> profile
        self.window_size = 20
        self.is_trained = False
        self.model_path = os.path.join(settings.ML_MODEL_DIR, "behavior_profiles.joblib")
        self._load_profiles()

    def _load_profiles(self):
        if os.path.exists(self.model_path):
            self.profiles = joblib.load(self.model_path)
            self.is_trained = bool(self.profiles)

    def _save_profiles(self):
        os.makedirs(settings.ML_MODEL_DIR, exist_ok=True)
        joblib.dump(self.profiles, self.model_path)

    def update_profile(self, device_id: int, features: np.ndarray):
        """Update the behavior profile for a device with new telemetry.

        Args:
            device_id: device identifier
            features: 1D array of feature values for one timestamp
        """
        if device_id not in self.profiles:
            self.profiles[device_id] = {
                "history": [],
                "mean": None,
                "std": None,
            }

        profile = self.profiles[device_id]
        profile["history"].append(features.tolist())

        # Keep only last N entries
        if len(profile["history"]) > self.window_size * 5:
            profile["history"] = profile["history"][-self.window_size * 5:]

        if len(profile["history"]) >= self.window_size:
            recent = np.array(profile["history"][-self.window_size:])
            profile["mean"] = recent.mean(axis=0).tolist()
            profile["std"] = (recent.std(axis=0) + 1e-6).tolist()
            self.is_trained = True

        self._save_profiles()

    def detect_deviation(self, device_id: int, features: np.ndarray) -> dict:
        """Detect if current behavior deviates from the learned profile.

        Returns:
            dict with deviation_score (0-1), is_deviation flag, and details
        """
        if device_id not in self.profiles or self.profiles[device_id]["mean"] is None:
            return {
                "deviation_score": 0.0,
                "is_deviation": False,
                "details": "Insufficient profile data",
            }

        profile = self.profiles[device_id]
        mean = np.array(profile["mean"])
        std = np.array(profile["std"])

        # Z-score based deviation detection
        z_scores = np.abs((features - mean) / std)
        max_z = float(np.max(z_scores))
        mean_z = float(np.mean(z_scores))

        # Normalize to 0-1 scale
        deviation_score = min(1.0, mean_z / 3.0)
        is_deviation = max_z > 3.0 or mean_z > 2.0

        # Find which features are most deviant
        feature_names = [
            "cpu_usage", "memory_usage", "disk_usage",
            "net_sent", "net_recv", "connections", "processes",
        ]
        deviant_features = []
        for i, (name, z) in enumerate(zip(feature_names[:len(z_scores)], z_scores)):
            if z > 2.0:
                deviant_features.append({"feature": name, "z_score": float(z)})

        return {
            "deviation_score": deviation_score,
            "is_deviation": is_deviation,
            "max_z_score": max_z,
            "mean_z_score": mean_z,
            "deviant_features": deviant_features,
            "details": f"{'Anomalous' if is_deviation else 'Normal'} behavior detected",
        }

    def get_status(self) -> dict:
        return {
            "model_name": "BehaviorProfiler",
            "trained": self.is_trained,
            "profiled_devices": len(self.profiles),
            "window_size": self.window_size,
        }
