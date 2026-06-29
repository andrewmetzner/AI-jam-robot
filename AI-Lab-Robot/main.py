#!/usr/bin/env python3
"""
LunaMind: Autonomous AI Scientist for Lunar Exploration

Orchestrates multimodal sensor fusion, computer vision, LLM reasoning,
and autonomous navigation to explore lunar terrain and identify
scientifically valuable samples.
"""

import argparse
import numpy as np
from pathlib import Path

from rover.rover import LunaMindRover
from sensors.camera import Camera
from sensors.depth import DepthSensor
from sensors.thermal import ThermalSensor
from sensors.spectral import SpectralAnalyzer
from ai.vision.rock_detector import RockDetector
from ai.vision.classifier import RockClassifier
from ai.fusion.sensor_fusion import SensorFusion
from ai.reasoning.scientist import LunarScientist
from ai.planning.route_planner import RoutePlanner


class MissionControl:
    def __init__(self, llm_client=None, model: str = "claude-opus"):
        """Initialize mission control system."""
        # Rover systems
        self.rover = LunaMindRover()

        # Sensors
        self.camera = Camera()
        self.depth_sensor = DepthSensor()
        self.thermal_sensor = ThermalSensor()
        self.spectral_analyzer = SpectralAnalyzer()

        # AI systems
        self.rock_detector = RockDetector()
        self.rock_classifier = RockClassifier()
        self.sensor_fusion = SensorFusion()
        self.scientist = LunarScientist(llm_client=llm_client, model=model)
        self.route_planner = RoutePlanner()

        # Mission state
        self.mission_log = []
        self.terrain_map = {}

    def execute_exploration_mission(
        self,
        num_locations: int = 5,
        terrain_type: str = "simple",
        use_llm: bool = False,
        generate_report: bool = True,
    ):
        """
        Execute autonomous exploration mission.
        Sense → Reason → Decide → Move → Explain
        """
        print(f"\n{'='*60}")
        print("LUNAMIND EXPLORATION MISSION INITIATED")
        print(f"{'='*60}\n")

        samples_found = []

        # Simulate exploring multiple locations
        for location_idx in range(num_locations):
            if not self.rover.is_operational():
                print(f"⚠️  Mission halted: Low battery ({self.rover.battery:.1f}%)")
                break

            print(f"\n📍 Exploring Location {location_idx + 1}/{num_locations}")
            print("-" * 40)

            # 1. SENSE: Capture multimodal sensor data
            sensor_data = self._sense(location_idx)
            print(f"✓ Sensors active: Camera, Depth, Thermal, Spectral")

            # 2. PROCESS: Fuse sensor data
            world_model = self.sensor_fusion.fuse(sensor_data)
            print(f"✓ Fused {len(world_model['rocks'])} rock detections")

            # 3. REASON: Analyze samples with AI scientist
            if world_model["rocks"]:
                location_samples = self._analyze_rocks(
                    world_model["rocks"], use_llm=use_llm
                )
                samples_found.extend(location_samples)
                print(f"✓ Analyzed {len(location_samples)} samples")

            # 4. DECIDE: Plan next movement
            next_location = self._plan_movement(location_idx, num_locations)
            print(f"✓ Next waypoint: {next_location}")

            # 5. MOVE: Execute navigation
            self.rover.move_to(next_location, step_size=0.2)
            print(f"✓ Rover position: {self.rover.get_state()['position']}")

        # EXPLAIN: Generate report
        if generate_report and samples_found:
            self._generate_report(samples_found)

        print(f"\n{'='*60}")
        print("MISSION COMPLETE")
        print(f"{'='*60}\n")

    def _sense(self, location_idx: int) -> dict:
        """Capture data from all sensors."""
        rocks = self.rock_detector.detect(np.random.randn(480, 640, 3))
        spectral = self.spectral_analyzer.analyze({})
        thermal_anomalies = self.thermal_sensor.detect_anomalies()

        return {
            "location": location_idx,
            "rocks": self.rock_detector.get_detections(),
            "spectral": spectral,
            "thermal_anomalies": thermal_anomalies,
            "depth": {"value": 5.0 + np.random.randn() * 1.0},
            "timestamp": location_idx,
        }

    def _analyze_rocks(self, rocks: list, use_llm: bool = False) -> list:
        """Analyze detected rocks using vision + spectral + LLM."""
        classifications = self.rock_classifier.classify(rocks)
        analyzed_samples = []

        for clf in classifications:
            sample = {
                "id": clf["id"],
                "type": clf["type"],
                "confidence": clf["confidence"],
                "visual_confidence": clf["visual_score"],
                "composition": {},
            }

            # Add spectral data
            spectral = self.spectral_analyzer.analyze({})
            sample["spectral_confidence"] = spectral.get("confidence", 0.7)

            # Analyze with scientist
            analysis = self.scientist.analyze_sample(sample)
            analyzed_samples.append(analysis)

        return analyzed_samples

    def _plan_movement(self, current_idx: int, total_locations: int) -> tuple:
        """Plan next movement waypoint."""
        if current_idx + 1 < total_locations:
            # Move to next exploration location
            return (current_idx + 2.0, 0.0)
        else:
            return self.rover.position  # Return to current position

    def _generate_report(self, samples: list):
        """Generate mission report with sample rankings."""
        print(f"\n{'='*60}")
        print("LUNAMIND SCIENCE REPORT")
        print(f"{'='*60}\n")

        ranked = self.scientist.rank_samples(samples)

        print(f"Mission Summary:")
        print(f"  - Samples Analyzed: {len(samples)}")
        print(f"  - Battery Remaining: {self.rover.battery:.1f}%")
        print(f"  - Samples Collected: {len(self.rover.samples_collected)}")

        print(f"\nTop 5 Scientifically Valuable Samples:\n")
        for i, sample in enumerate(ranked[:5], 1):
            print(
                f"{i}. Sample #{sample['sample_id']} ({sample['rock_type'].upper()})"
            )
            print(f"   Scientific Value: {sample['scientific_value']:.2f}")
            if "explanation" in sample:
                print(f"   Notes: {sample['explanation'][:100]}...")
            print()

        print(f"\nHazards Detected: {len([s for s in samples if s.get('hazard')])}")
        print(f"\nRecommendations:")
        print(f"  - Prioritize high-value olivine and anorthosite samples")
        print(f"  - Return to base when battery < 10%")
        print(f"  - Next mission should explore southern plateau")


def main():
    parser = argparse.ArgumentParser(description="LunaMind Autonomous Rover Mission")
    parser.add_argument(
        "--mission",
        default="explore",
        choices=["explore", "sample_collection", "hazard_assessment"],
        help="Mission type",
    )
    parser.add_argument(
        "--terrain",
        default="simple",
        choices=["simple", "complex", "hazard", "realistic"],
        help="Terrain type",
    )
    parser.add_argument(
        "--locations", type=int, default=5, help="Number of exploration locations"
    )
    parser.add_argument(
        "--use-llm", action="store_true", help="Enable LLM-based reasoning"
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        default=True,
        help="Generate mission report",
    )
    parser.add_argument(
        "--model", default="claude-opus", help="LLM model to use"
    )

    args = parser.parse_args()

    # Initialize mission control
    llm_client = None
    if args.use_llm:
        try:
            from anthropic import Anthropic

            llm_client = Anthropic()
            print("✓ LLM integration enabled (Claude)\n")
        except ImportError:
            print("⚠️  Anthropic SDK not available. Running without LLM.\n")

    mission = MissionControl(llm_client=llm_client, model=args.model)

    # Execute mission
    if args.mission == "explore":
        mission.execute_exploration_mission(
            num_locations=args.locations,
            terrain_type=args.terrain,
            use_llm=args.use_llm,
            generate_report=args.generate_report,
        )


if __name__ == "__main__":
    main()
