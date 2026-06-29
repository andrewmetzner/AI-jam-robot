"""Depth sensor for rover 3D perception."""

import numpy as np
from typing import Tuple


class DepthSensor:
    def __init__(self, resolution: Tuple[int, int] = (640, 480), max_range: float = 10.0):
        """Initialize depth sensor."""
        self.resolution = resolution
        self.max_range = max_range
        self.depth_map = None

    def capture(self, scene_data: dict) -> np.ndarray:
        """Capture depth map from simulated scene."""
        if "depth_map" in scene_data:
            self.depth_map = scene_data["depth_map"]
        else:
            self.depth_map = np.random.uniform(0, self.max_range, self.resolution)
        return self.depth_map

    def get_depth_map(self) -> np.ndarray:
        """Get latest depth map."""
        return self.depth_map

    def get_3d_points(self, camera_intrinsics: dict) -> np.ndarray:
        """Convert depth map to 3D point cloud."""
        if self.depth_map is None:
            return None

        h, w = self.resolution
        x = np.arange(w)
        y = np.arange(h)
        xx, yy = np.meshgrid(x, y)

        fx = camera_intrinsics["fx"]
        fy = camera_intrinsics["fy"]
        cx = camera_intrinsics["cx"]
        cy = camera_intrinsics["cy"]

        z = self.depth_map
        x_3d = (xx - cx) * z / fx
        y_3d = (yy - cy) * z / fy
        z_3d = z

        points = np.stack([x_3d, y_3d, z_3d], axis=-1)
        return points.reshape(-1, 3)
