"""Thermal imaging sensor for hazard detection."""

import numpy as np
from typing import Tuple


class ThermalSensor:
    def __init__(self, resolution: Tuple[int, int] = (320, 240)):
        """Initialize thermal sensor."""
        self.resolution = resolution
        self.thermal_map = None

    def capture(self, scene_data: dict) -> np.ndarray:
        """Capture thermal image from simulated scene."""
        if "thermal_map" in scene_data:
            self.thermal_map = scene_data["thermal_map"]
        else:
            self.thermal_map = np.random.normal(250, 20, self.resolution)
        return self.thermal_map

    def detect_anomalies(self, threshold: float = 280.0) -> list:
        """Detect thermal anomalies (e.g., overheating equipment)."""
        if self.thermal_map is None:
            return []

        anomalies = []
        hot_regions = self.thermal_map > threshold
        if np.any(hot_regions):
            coords = np.argwhere(hot_regions)
            for y, x in coords:
                anomalies.append({
                    "position": (x, y),
                    "temperature": float(self.thermal_map[y, x]),
                    "severity": min(1.0, (self.thermal_map[y, x] - threshold) / 50),
                })
        return anomalies

    def get_thermal_map(self) -> np.ndarray:
        """Get latest thermal map."""
        return self.thermal_map
