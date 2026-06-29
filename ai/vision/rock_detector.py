"""Rock detection using computer vision."""

import numpy as np
from typing import List, Tuple


class RockDetector:
    def __init__(self):
        """Initialize rock detector."""
        self.detections = []

    def detect(self, image: np.ndarray) -> List[dict]:
        """
        Detect rocks in image.
        Returns list of bounding boxes with confidence scores.
        """
        if image is None or image.size == 0:
            return []

        detections = []

        # Placeholder: simulate rock detection
        # In practice, this would use YOLO or DETR
        num_rocks = np.random.randint(1, 6)
        h, w = image.shape[:2]

        for i in range(num_rocks):
            x = np.random.randint(0, w - 50)
            y = np.random.randint(0, h - 50)
            width = np.random.randint(30, 100)
            height = np.random.randint(30, 100)
            confidence = np.random.uniform(0.7, 0.99)

            detections.append({
                "id": i,
                "bbox": (x, y, width, height),  # (x, y, w, h)
                "confidence": confidence,
                "class": "rock",
            })

        self.detections = detections
        return detections

    def get_detections(self) -> List[dict]:
        """Get latest detections."""
        return self.detections

    def filter_by_confidence(self, threshold: float = 0.8) -> List[dict]:
        """Filter detections by confidence threshold."""
        return [d for d in self.detections if d["confidence"] >= threshold]
