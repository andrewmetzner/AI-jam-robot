"""Rock classification system."""

import numpy as np
from typing import List, Dict


class RockClassifier:
    def __init__(self):
        """Initialize rock classifier."""
        self.rock_classes = ["basalt", "olivine", "anorthosite", "regolith", "unknown"]
        self.classifications = []

    def classify(self, detections: List[dict], spectral_data: dict = None) -> List[dict]:
        """
        Classify detected rocks into geological types.
        Combines visual and spectral features.
        """
        classifications = []

        for det in detections:
            rock_id = det["id"]

            # Use spectral data if available, otherwise use visual features
            if spectral_data and "rock_type" in spectral_data:
                rock_type = spectral_data["rock_type"]
                confidence = spectral_data.get("confidence", 0.8)
            else:
                # Simulated visual classification
                rock_type = np.random.choice(self.rock_classes[:-1])
                confidence = np.random.uniform(0.65, 0.95)

            classifications.append({
                "id": rock_id,
                "type": rock_type,
                "confidence": confidence,
                "bbox": det["bbox"],
                "visual_score": np.random.uniform(0.6, 0.9),
            })

        self.classifications = classifications
        return classifications

    def get_classifications(self) -> List[dict]:
        """Get latest classifications."""
        return self.classifications

    def get_high_confidence(self, threshold: float = 0.8) -> List[dict]:
        """Get only high-confidence classifications."""
        return [c for c in self.classifications if c["confidence"] >= threshold]

    def get_by_type(self, rock_type: str) -> List[dict]:
        """Get all rocks of a specific type."""
        return [c for c in self.classifications if c["type"] == rock_type]
