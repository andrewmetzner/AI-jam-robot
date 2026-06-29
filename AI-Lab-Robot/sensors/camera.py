"""RGB camera sensor for rover."""

import numpy as np
from typing import Tuple


class Camera:
    def __init__(self, resolution: Tuple[int, int] = (640, 480), fov: float = 90.0):
        """Initialize camera sensor."""
        self.resolution = resolution
        self.fov = fov
        self.intrinsics = self._compute_intrinsics()
        self.frame = None

    def _compute_intrinsics(self) -> dict:
        """Compute camera intrinsic parameters."""
        w, h = self.resolution
        focal_length = (w / 2) / np.tan(np.radians(self.fov / 2))
        return {
            "fx": focal_length,
            "fy": focal_length,
            "cx": w / 2,
            "cy": h / 2,
        }

    def capture(self, scene_data: dict) -> np.ndarray:
        """Capture RGB frame from simulated scene."""
        if "renderer" in scene_data:
            pixels = scene_data["renderer"].render()
            self.frame = pixels[:, :, :3]  # RGB only
            return self.frame
        else:
            self.frame = np.zeros((*self.resolution, 3), dtype=np.uint8)
            return self.frame

    def get_frame(self) -> np.ndarray:
        """Get latest captured frame."""
        return self.frame

    def get_intrinsics(self) -> dict:
        """Get camera intrinsic parameters."""
        return self.intrinsics
