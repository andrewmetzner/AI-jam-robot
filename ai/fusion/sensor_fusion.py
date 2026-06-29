"""Multimodal sensor fusion for world model."""

from typing import Dict, List
import numpy as np


class SensorFusion:
    def __init__(self):
        """Initialize sensor fusion engine."""
        self.world_model = {}
        self.spatial_map = {}
        self.uncertainty_map = {}

    def fuse(self, sensor_data: Dict) -> Dict:
        """
        Fuse data from multiple sensors:
        - Camera (rock detection)
        - Depth (spatial mapping)
        - Thermal (hazard detection)
        - Spectral (composition analysis)
        """
        fused_data = {
            "rocks": [],
            "hazards": [],
            "obstacles": [],
            "timestamp": sensor_data.get("timestamp", 0),
        }

        # Fuse rock detections with spectral analysis
        if "rocks" in sensor_data:
            fused_data["rocks"] = self._fuse_rock_data(
                sensor_data["rocks"],
                sensor_data.get("spectral", None),
                sensor_data.get("depth", None),
            )

        # Fuse thermal anomalies with depth for hazard mapping
        if "thermal_anomalies" in sensor_data:
            fused_data["hazards"] = self._fuse_hazard_data(
                sensor_data["thermal_anomalies"],
                sensor_data.get("depth", None),
            )

        # Detect obstacles from depth
        if "depth" in sensor_data:
            fused_data["obstacles"] = self._detect_obstacles(sensor_data["depth"])

        self.world_model = fused_data
        return fused_data

    def _fuse_rock_data(self, rocks: List[dict], spectral: dict, depth: dict) -> List[dict]:
        """Fuse visual rock detection with spectral and depth data."""
        fused_rocks = []
        for rock in rocks:
            rock_id = rock.get("id")
            fused_rock = {
                "id": rock_id,
                "bbox": rock.get("bbox"),
                "visual_confidence": rock.get("confidence", 0.8),
                "depth_estimate": depth.get("value", 5.0) if depth else 5.0,
            }

            if spectral:
                fused_rock["spectral_type"] = spectral.get("rock_type", "unknown")
                fused_rock["composition"] = spectral.get("composition", {})
                fused_rock["spectral_confidence"] = spectral.get("confidence", 0.7)
                # Combined confidence = average of visual + spectral
                fused_rock["combined_confidence"] = (
                    fused_rock["visual_confidence"] + fused_rock["spectral_confidence"]
                ) / 2
            else:
                fused_rock["combined_confidence"] = fused_rock["visual_confidence"]

            fused_rocks.append(fused_rock)

        return fused_rocks

    def _fuse_hazard_data(self, thermal_anomalies: List[dict], depth: dict) -> List[dict]:
        """Fuse thermal anomalies with spatial data."""
        hazards = []
        for anomaly in thermal_anomalies:
            hazard = {
                "type": "thermal",
                "position": anomaly.get("position", (0, 0)),
                "temperature": anomaly.get("temperature", 300),
                "severity": anomaly.get("severity", 0.5),
                "depth_estimate": depth.get("value", 3.0) if depth else 3.0,
            }
            hazards.append(hazard)
        return hazards

    def _detect_obstacles(self, depth_map: dict) -> List[dict]:
        """Detect obstacles from depth data."""
        obstacles = []
        if "values" in depth_map:
            depths = depth_map["values"]
            min_safe_depth = 0.5
            if np.any(depths < min_safe_depth):
                obstacles.append({
                    "type": "depth_obstacle",
                    "min_distance": float(np.min(depths)),
                    "severity": 1.0 - (np.min(depths) / min_safe_depth),
                })
        return obstacles

    def get_world_model(self) -> Dict:
        """Get current fused world model."""
        return self.world_model
