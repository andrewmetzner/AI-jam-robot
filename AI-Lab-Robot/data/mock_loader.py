"""Mock data loader for LunaMind testing and development."""

import numpy as np
from typing import Dict, List, Tuple


class MockDataLoader:
    """Load simulated sensor data for testing without real hardware."""

    def __init__(self, seed: int = 42):
        """Initialize mock data loader."""
        np.random.seed(seed)
        self.rock_types = ["basalt", "olivine", "anorthosite", "regolith"]
        self.element_profiles = {
            "basalt": {"Fe": 0.15, "Mg": 0.12, "Si": 0.25, "Ca": 0.08, "Al": 0.10},
            "olivine": {"Mg": 0.30, "Fe": 0.20, "Si": 0.18, "Ca": 0.02},
            "anorthosite": {"Al": 0.25, "Si": 0.28, "Ca": 0.15, "Mg": 0.05},
            "regolith": {"Si": 0.22, "Fe": 0.08, "Mg": 0.08, "Al": 0.12, "O": 0.20},
        }

    def get_simulated_rocks(self, num_rocks: int = 5) -> List[Dict]:
        """Generate simulated rock detection data."""
        rocks = []
        for i in range(num_rocks):
            rock_type = np.random.choice(self.rock_types)
            rocks.append({
                "id": i,
                "type": rock_type,
                "confidence": np.random.uniform(0.65, 0.99),
                "bbox": self._random_bbox(),
                "depth": np.random.uniform(2.0, 10.0),
            })
        return rocks

    def get_simulated_spectral_data(self, rock_type: str = None) -> Dict:
        """Generate simulated spectral analysis data."""
        if rock_type is None:
            rock_type = np.random.choice(self.rock_types)

        base_comp = self.element_profiles[rock_type]
        noisy_comp = {k: v + np.random.normal(0, 0.02) for k, v in base_comp.items()}
        noisy_comp = {k: max(0, v) for k, v in noisy_comp.items()}

        return {
            "rock_type": rock_type,
            "composition": noisy_comp,
            "confidence": np.random.uniform(0.70, 0.95),
            "elements": list(noisy_comp.keys()),
        }

    def get_simulated_terrain_map(self, width: int = 100, height: int = 100) -> np.ndarray:
        """Generate simulated terrain elevation map."""
        x = np.linspace(0, 10, width)
        y = np.linspace(0, 10, height)
        X, Y = np.meshgrid(x, y)
        terrain = (
            5
            + 2 * np.sin(X / 3)
            + 1.5 * np.cos(Y / 3)
            + 0.5 * np.random.randn(height, width)
        )
        return terrain

    def get_simulated_hazards(self, num_hazards: int = 3) -> List[Dict]:
        """Generate simulated hazard data (radiation, thermal, etc)."""
        hazards = []
        for i in range(num_hazards):
            hazard_type = np.random.choice(["radiation", "thermal", "chemical"])
            hazards.append({
                "id": i,
                "type": hazard_type,
                "position": (np.random.uniform(0, 100), np.random.uniform(0, 100)),
                "intensity": np.random.uniform(0.3, 1.0),
                "severity": np.random.uniform("low", "high") if hazard_type == "radiation" else "medium",
            })
        return hazards

    def get_simulated_mission_data(self, num_locations: int = 5) -> Dict:
        """Generate complete mission dataset."""
        mission_data = {
            "mission_id": "LUNAR_EXPLORATION_001",
            "terrain_map": self.get_simulated_terrain_map(),
            "locations": [],
        }

        for loc_idx in range(num_locations):
            location_data = {
                "location_id": loc_idx,
                "position": (loc_idx * 20, np.random.uniform(20, 80)),
                "rocks": self.get_simulated_rocks(num_rocks=np.random.randint(2, 6)),
                "spectral_data": [
                    self.get_simulated_spectral_data() for _ in range(np.random.randint(1, 4))
                ],
                "hazards": self.get_simulated_hazards(num_hazards=np.random.randint(0, 3)),
                "timestamp": loc_idx * 300,  # seconds
            }
            mission_data["locations"].append(location_data)

        return mission_data

    def get_benchmark_dataset(self) -> Dict:
        """Get standardized benchmark dataset for evaluation."""
        return {
            "name": "LunarBench-v1",
            "terrain": "simple",
            "num_samples": 23,
            "num_hazards": 2,
            "ground_truth": {
                "valuable_samples": [8, 14, 3, 19, 11],  # Sample IDs
                "hazard_zones": [
                    {"type": "radiation", "severity": "high"},
                    {"type": "thermal", "severity": "medium"},
                ],
            },
            "mission_data": self.get_simulated_mission_data(num_locations=5),
        }

    @staticmethod
    def _random_bbox() -> Tuple[int, int, int, int]:
        """Generate random bounding box coordinates."""
        x = np.random.randint(0, 590)
        y = np.random.randint(0, 430)
        w = np.random.randint(30, 100)
        h = np.random.randint(30, 100)
        return (x, y, w, h)


class DatasetExporter:
    """Export mock data to various formats."""

    @staticmethod
    def export_to_json(data: Dict, filepath: str):
        """Export mock data to JSON file."""
        import json
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Exported to {filepath}")

    @staticmethod
    def export_to_csv(rocks: List[Dict], filepath: str):
        """Export rock data to CSV."""
        import csv
        if not rocks:
            return

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rocks[0].keys())
            writer.writeheader()
            writer.writerows(rocks)
        print(f"Exported to {filepath}")


# Example usage for testing
if __name__ == "__main__":
    loader = MockDataLoader()

    # Generate mission data
    mission = loader.get_simulated_mission_data(num_locations=3)
    print(f"Generated mission with {len(mission['locations'])} locations")

    # Get benchmark dataset
    benchmark = loader.get_benchmark_dataset()
    print(f"Benchmark dataset: {benchmark['name']} - {benchmark['num_samples']} samples")

    # Export example
    exporter = DatasetExporter()
    exporter.export_to_json(mission, "mission_data.json")
