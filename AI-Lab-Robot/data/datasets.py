"""Pre-built mock datasets for mission testing."""

import numpy as np
from typing import Dict, List


class MissionDatasets:
    """Collection of realistic mission scenarios."""

    @staticmethod
    def simple_survey() -> Dict:
        """Easy terrain with 5 clear rock outcrops."""
        return {
            "name": "Simple Survey",
            "description": "Flat terrain, isolated rocks, ideal for beginner testing",
            "terrain_difficulty": "easy",
            "num_locations": 5,
            "locations": [
                {
                    "id": 0,
                    "position": (0, 0),
                    "rocks": [
                        {"id": 0, "type": "basalt", "confidence": 0.92, "bbox": (100, 150, 80, 70)},
                        {"id": 1, "type": "olivine", "confidence": 0.88, "bbox": (300, 200, 90, 85)},
                    ],
                    "hazards": [],
                    "terrain_slope": 0.0,
                },
                {
                    "id": 1,
                    "position": (25, 0),
                    "rocks": [
                        {"id": 2, "type": "anorthosite", "confidence": 0.85, "bbox": (150, 300, 100, 95)},
                    ],
                    "hazards": [],
                    "terrain_slope": 2.0,
                },
                {
                    "id": 2,
                    "position": (50, 0),
                    "rocks": [
                        {"id": 3, "type": "basalt", "confidence": 0.90, "bbox": (200, 250, 85, 75)},
                        {"id": 4, "type": "regolith", "confidence": 0.75, "bbox": (350, 350, 60, 50)},
                    ],
                    "hazards": [],
                    "terrain_slope": 1.5,
                },
                {
                    "id": 3,
                    "position": (75, 0),
                    "rocks": [
                        {"id": 5, "type": "olivine", "confidence": 0.91, "bbox": (180, 200, 110, 100)},
                    ],
                    "hazards": [],
                    "terrain_slope": 0.5,
                },
                {
                    "id": 4,
                    "position": (100, 0),
                    "rocks": [
                        {"id": 6, "type": "anorthosite", "confidence": 0.87, "bbox": (250, 280, 95, 90)},
                        {"id": 7, "type": "basalt", "confidence": 0.89, "bbox": (100, 100, 75, 70)},
                    ],
                    "hazards": [],
                    "terrain_slope": 0.0,
                },
            ],
            "ground_truth_valuable": [1, 2, 5, 6],  # Olivine, Anorthosite rocks
        }

    @staticmethod
    def complex_terrain() -> Dict:
        """Challenging terrain with slopes, obstacles, and mixed hazards."""
        return {
            "name": "Complex Terrain",
            "description": "Hilly terrain, navigation hazards, thermal anomalies",
            "terrain_difficulty": "hard",
            "num_locations": 6,
            "locations": [
                {
                    "id": 0,
                    "position": (0, 0),
                    "rocks": [
                        {"id": 0, "type": "basalt", "confidence": 0.85, "bbox": (150, 200, 70, 65)},
                    ],
                    "hazards": [],
                    "terrain_slope": 5.0,
                },
                {
                    "id": 1,
                    "position": (20, 15),
                    "rocks": [
                        {"id": 1, "type": "olivine", "confidence": 0.92, "bbox": (180, 250, 95, 90)},
                        {"id": 2, "type": "basalt", "confidence": 0.80, "bbox": (300, 300, 60, 55)},
                    ],
                    "hazards": [
                        {"type": "thermal", "severity": "medium", "position": (350, 200), "intensity": 0.6}
                    ],
                    "terrain_slope": 8.0,
                },
                {
                    "id": 2,
                    "position": (40, 25),
                    "rocks": [
                        {"id": 3, "type": "anorthosite", "confidence": 0.88, "bbox": (120, 180, 105, 100)},
                    ],
                    "hazards": [
                        {"type": "radiation", "severity": "high", "position": (200, 150), "intensity": 0.8}
                    ],
                    "terrain_slope": 12.0,
                },
                {
                    "id": 3,
                    "position": (55, 30),
                    "rocks": [
                        {"id": 4, "type": "regolith", "confidence": 0.70, "bbox": (220, 280, 65, 60)},
                    ],
                    "hazards": [],
                    "terrain_slope": 3.0,
                },
                {
                    "id": 4,
                    "position": (70, 20),
                    "rocks": [
                        {"id": 5, "type": "olivine", "confidence": 0.89, "bbox": (160, 220, 90, 85)},
                    ],
                    "hazards": [
                        {"type": "thermal", "severity": "low", "position": (300, 280), "intensity": 0.4}
                    ],
                    "terrain_slope": 6.5,
                },
                {
                    "id": 5,
                    "position": (85, 10),
                    "rocks": [
                        {"id": 6, "type": "basalt", "confidence": 0.86, "bbox": (200, 240, 80, 75)},
                    ],
                    "hazards": [],
                    "terrain_slope": 4.0,
                },
            ],
            "ground_truth_valuable": [1, 3, 5],
        }

    @staticmethod
    def crater_exploration() -> Dict:
        """Deep crater with subsurface access opportunities."""
        return {
            "name": "Crater Exploration",
            "description": "Crater rim survey with coring opportunities",
            "terrain_difficulty": "medium",
            "num_locations": 7,
            "locations": [
                {
                    "id": 0,
                    "position": (0, 0),
                    "rocks": [
                        {"id": 0, "type": "basalt", "confidence": 0.84, "bbox": (150, 200, 75, 70)},
                    ],
                    "hazards": [],
                    "terrain_slope": 15.0,
                    "coring_opportunity": True,
                    "subsurface_composition": {"type": "olivine-rich", "confidence": 0.75},
                },
                {
                    "id": 1,
                    "position": (20, -20),
                    "rocks": [
                        {"id": 1, "type": "olivine", "confidence": 0.93, "bbox": (180, 240, 100, 95)},
                        {"id": 2, "type": "anorthosite", "confidence": 0.87, "bbox": (320, 280, 85, 80)},
                    ],
                    "hazards": [],
                    "terrain_slope": 20.0,
                    "coring_opportunity": True,
                    "subsurface_composition": {"type": "mixed_olivine_anorthosite", "confidence": 0.80},
                },
                {
                    "id": 2,
                    "position": (35, -35),
                    "rocks": [
                        {"id": 3, "type": "anorthosite", "confidence": 0.90, "bbox": (140, 190, 110, 105)},
                    ],
                    "hazards": [
                        {"type": "radiation", "severity": "medium", "position": (250, 200), "intensity": 0.65}
                    ],
                    "terrain_slope": 25.0,
                    "coring_opportunity": True,
                    "subsurface_composition": {"type": "plagioclase-rich", "confidence": 0.85},
                },
                {
                    "id": 3,
                    "position": (40, -10),
                    "rocks": [],
                    "hazards": [],
                    "terrain_slope": 5.0,
                    "coring_opportunity": False,
                },
                {
                    "id": 4,
                    "position": (50, -25),
                    "rocks": [
                        {"id": 4, "type": "basalt", "confidence": 0.88, "bbox": (170, 210, 85, 80)},
                    ],
                    "hazards": [],
                    "terrain_slope": 18.0,
                    "coring_opportunity": True,
                    "subsurface_composition": {"type": "basaltic_lava_flows", "confidence": 0.78},
                },
                {
                    "id": 5,
                    "position": (60, -35),
                    "rocks": [
                        {"id": 5, "type": "olivine", "confidence": 0.91, "bbox": (190, 250, 95, 90)},
                    ],
                    "hazards": [
                        {"type": "thermal", "severity": "medium", "position": (280, 220), "intensity": 0.7}
                    ],
                    "terrain_slope": 22.0,
                    "coring_opportunity": True,
                    "subsurface_composition": {"type": "olivine_dunite", "confidence": 0.82},
                },
                {
                    "id": 6,
                    "position": (75, -15),
                    "rocks": [
                        {"id": 6, "type": "anorthosite", "confidence": 0.86, "bbox": (160, 200, 100, 95)},
                    ],
                    "hazards": [],
                    "terrain_slope": 12.0,
                    "coring_opportunity": True,
                    "subsurface_composition": {"type": "highlands_material", "confidence": 0.80},
                },
            ],
            "ground_truth_valuable": [1, 2, 5, 6],
        }

    @staticmethod
    def hazardous_zone() -> Dict:
        """High-radiation or thermally active region. Tests risk assessment."""
        return {
            "name": "Hazardous Zone",
            "description": "Radiation hotspot with few accessible samples",
            "terrain_difficulty": "hard",
            "num_locations": 4,
            "locations": [
                {
                    "id": 0,
                    "position": (0, 0),
                    "rocks": [
                        {"id": 0, "type": "basalt", "confidence": 0.82, "bbox": (150, 200, 70, 65)},
                    ],
                    "hazards": [
                        {"type": "radiation", "severity": "high", "position": (200, 150), "intensity": 0.95}
                    ],
                    "terrain_slope": 2.0,
                    "radiation_dose_rate": 500,  # mSv/year
                },
                {
                    "id": 1,
                    "position": (30, 0),
                    "rocks": [
                        {"id": 1, "type": "olivine", "confidence": 0.85, "bbox": (180, 240, 90, 85)},
                    ],
                    "hazards": [
                        {"type": "radiation", "severity": "high", "position": (150, 200), "intensity": 0.90},
                        {"type": "thermal", "severity": "high", "position": (280, 280), "intensity": 0.85},
                    ],
                    "terrain_slope": 1.0,
                    "radiation_dose_rate": 750,  # mSv/year
                },
                {
                    "id": 2,
                    "position": (50, 15),
                    "rocks": [
                        {"id": 2, "type": "anorthosite", "confidence": 0.89, "bbox": (140, 180, 105, 100)},
                    ],
                    "hazards": [
                        {"type": "radiation", "severity": "critical", "position": (100, 100), "intensity": 0.98}
                    ],
                    "terrain_slope": 0.5,
                    "radiation_dose_rate": 1200,  # mSv/year - AVOID ZONE
                },
                {
                    "id": 3,
                    "position": (70, 0),
                    "rocks": [
                        {"id": 3, "type": "basalt", "confidence": 0.83, "bbox": (160, 210, 80, 75)},
                    ],
                    "hazards": [
                        {"type": "radiation", "severity": "medium", "position": (250, 200), "intensity": 0.60}
                    ],
                    "terrain_slope": 1.5,
                    "radiation_dose_rate": 300,  # mSv/year
                },
            ],
            "ground_truth_valuable": [1],  # Only one safe high-value sample
            "note": "Mission requires hazard awareness and selective sampling",
        }

    @staticmethod
    def subsurface_drill_sites() -> Dict:
        """Targets for deep drilling and core extraction."""
        return {
            "name": "Subsurface Drill Sites",
            "description": "Locations optimized for coring and subsurface sampling",
            "terrain_difficulty": "medium",
            "num_locations": 5,
            "locations": [
                {
                    "id": 0,
                    "position": (0, 0),
                    "rocks": [
                        {"id": 0, "type": "basalt", "confidence": 0.86, "bbox": (150, 200, 80, 75)},
                    ],
                    "drill_targets": [
                        {"depth": 1.0, "expected_type": "basalt", "priority": "high"},
                        {"depth": 2.0, "expected_type": "olivine", "priority": "medium"},
                    ],
                    "terrain_slope": 0.0,
                },
                {
                    "id": 1,
                    "position": (25, 0),
                    "rocks": [
                        {"id": 1, "type": "olivine", "confidence": 0.90, "bbox": (180, 240, 95, 90)},
                    ],
                    "drill_targets": [
                        {"depth": 1.5, "expected_type": "olivine-rich", "priority": "critical"},
                        {"depth": 3.0, "expected_type": "mantle_material", "priority": "high"},
                    ],
                    "terrain_slope": 1.0,
                },
                {
                    "id": 2,
                    "position": (50, 0),
                    "rocks": [
                        {"id": 2, "type": "anorthosite", "confidence": 0.88, "bbox": (140, 190, 105, 100)},
                    ],
                    "drill_targets": [
                        {"depth": 0.5, "expected_type": "highland_material", "priority": "high"},
                        {"depth": 2.5, "expected_type": "original_crust", "priority": "critical"},
                    ],
                    "terrain_slope": 0.5,
                },
                {
                    "id": 3,
                    "position": (75, 0),
                    "rocks": [],
                    "drill_targets": [
                        {"depth": 2.0, "expected_type": "subsurface_ice", "priority": "critical"},
                    ],
                    "terrain_slope": 0.0,
                },
                {
                    "id": 4,
                    "position": (100, 0),
                    "rocks": [
                        {"id": 3, "type": "regolith", "confidence": 0.75, "bbox": (200, 250, 70, 65)},
                    ],
                    "drill_targets": [
                        {"depth": 1.0, "expected_type": "space_weathered_material", "priority": "medium"},
                    ],
                    "terrain_slope": 0.0,
                },
            ],
            "ground_truth_valuable": [1, 2],
        }

    @staticmethod
    def radar_survey() -> Dict:
        """Real mock radar observations converted to mission format."""
        try:
            from data.radar_dataset import RadarMissionDataset
            mission = RadarMissionDataset.load_radar_mission()
            if mission:
                return mission
        except Exception as e:
            print(f"Warning: Could not load radar dataset: {e}")

        # Fallback to simple dataset if radar loading fails
        return {
            "name": "Radar Survey",
            "description": "Real mock radar observations from mock_radar_observations_1hour.csv",
            "terrain_difficulty": "medium",
            "num_locations": 0,
            "locations": [],
            "source": "datasets/mock_radar_observations_1hour.csv",
        }

    @staticmethod
    def all_datasets() -> Dict[str, Dict]:
        """Return all available datasets."""
        return {
            "simple": MissionDatasets.simple_survey(),
            "complex": MissionDatasets.complex_terrain(),
            "crater": MissionDatasets.crater_exploration(),
            "hazard": MissionDatasets.hazardous_zone(),
            "drill": MissionDatasets.subsurface_drill_sites(),
            "radar": MissionDatasets.radar_survey(),
        }


class DatasetLoader:
    """Load datasets for testing."""

    @staticmethod
    def load_dataset(name: str) -> Dict:
        """Load a dataset by name."""
        datasets = MissionDatasets.all_datasets()
        if name not in datasets:
            raise ValueError(
                f"Unknown dataset '{name}'. Available: {list(datasets.keys())}"
            )
        return datasets[name]

    @staticmethod
    def list_datasets() -> List[str]:
        """List all available datasets."""
        return list(MissionDatasets.all_datasets().keys())

    @staticmethod
    def get_dataset_info() -> Dict[str, str]:
        """Get descriptions of all datasets."""
        datasets = MissionDatasets.all_datasets()
        return {
            name: data.get("description", "No description")
            for name, data in datasets.items()
        }


if __name__ == "__main__":
    print("Available Datasets:\n")
    for name, desc in DatasetLoader.get_dataset_info().items():
        print(f"  {name:12} - {desc}")

    print("\n\nExample: Loading 'simple' dataset")
    dataset = DatasetLoader.load_dataset("simple")
    print(f"  Name: {dataset['name']}")
    print(f"  Locations: {dataset['num_locations']}")
    print(f"  Valuable samples: {dataset['ground_truth_valuable']}")
