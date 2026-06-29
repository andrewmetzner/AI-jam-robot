#!/usr/bin/env python3
"""
Autonomous Rover Mission Control - Interactive & CLI Mode

Usage:
  python main.py                    # Launch interactive menu
  python main.py --dataset simple   # Direct CLI mode
"""

import argparse
import sys
import os
from pathlib import Path

# Import all rover systems
import numpy as np
from rover.rover import Rover
from sensors.camera import Camera
from sensors.depth import DepthSensor
from sensors.thermal import ThermalSensor
from sensors.spectral import SpectralAnalyzer
from ai.vision.rock_detector import RockDetector
from ai.vision.classifier import RockClassifier
from ai.fusion.sensor_fusion import SensorFusion
from ai.reasoning.scientist import Scientist
from ai.planning.route_planner import RoutePlanner


def clear_screen():
    """Clear terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    """Print welcome banner."""
    print("""
+============================================================================+
|                                                                            |
|                    AUTONOMOUS ROVER MISSION CONTROL                        |
|                       2040s Lunar Research Station                         |
|                                                                            |
+============================================================================+
    """)


def print_main_menu():
    """Print main menu options."""
    print("\n" + "="*70)
    print("MAIN MENU - Select an Option")
    print("="*70 + "\n")
    print("  1. View Available Datasets")
    print("  2. Run Mission with Dataset")
    print("  3. View Mission Reports")
    print("  4. Test ML Models")
    print("  5. Astronaut Health Monitoring Demo")
    print("  6. Exit\n")


def print_dataset_menu():
    """Print dataset selection menu."""
    datasets = {
        "1": {"name": "Simple Survey", "key": "simple", "desc": "Flat terrain, isolated rocks (Easy)"},
        "2": {"name": "Complex Terrain", "key": "complex", "desc": "Hills, slopes, hazards (Hard)"},
        "3": {"name": "Crater Exploration", "key": "crater", "desc": "Subsurface drilling (Medium)"},
        "4": {"name": "Hazardous Zone", "key": "hazard", "desc": "High radiation (Hard - Risk)"},
        "5": {"name": "Drill Sites", "key": "drill", "desc": "Deep coring targets (Medium)"},
    }

    print("\n" + "="*70)
    print("AVAILABLE DATASETS")
    print("="*70 + "\n")

    for num, dataset in datasets.items():
        print(f"  {num}. {dataset['name']:20} - {dataset['desc']}")

    print("\n  0. Back to Main Menu\n")
    return datasets


def print_mission_menu():
    """Print mission type selection menu."""
    missions = {
        "1": {"name": "Exploration", "key": "explore", "desc": "Autonomous terrain survey"},
        "2": {"name": "Sample Collection", "key": "sample_collection", "desc": "Focused sampling mission"},
        "3": {"name": "Hazard Assessment", "key": "hazard_assessment", "desc": "Risk evaluation survey"},
    }

    print("\n" + "="*70)
    print("MISSION TYPES")
    print("="*70 + "\n")

    for num, mission in missions.items():
        print(f"  {num}. {mission['name']:20} - {mission['desc']}")

    print("\n  0. Back to Menu\n")
    return missions


def print_llm_menu():
    """Print LLM options menu."""
    print("\n" + "="*70)
    print("LLM REASONING")
    print("="*70 + "\n")
    print("  1. Enable LLM Reasoning (Claude API)")
    print("  2. Disable LLM Reasoning (Heuristic only)")
    print("\n  0. Back to Menu\n")


def run_mission(dataset_key: str, mission_key: str, use_llm: bool = False):
    """Execute mission with selected parameters."""
    print("\n" + "="*70)
    print("LAUNCHING MISSION...")
    print("="*70 + "\n")

    cmd = f"python main.py --dataset {dataset_key} --mission {mission_key} --generate-report"
    if use_llm:
        cmd += " --use-llm"

    print(f"Dataset: {dataset_key}")
    print(f"Mission: {mission_key}")
    print(f"LLM Enabled: {use_llm}\n")
    print("Starting mission in 2 seconds...\n")

    import time
    time.sleep(2)

    os.system(cmd)

    print("\n" + "="*70)
    print("MISSION COMPLETE")
    print("="*70)
    input("\nPress ENTER to return to main menu...")


def run_ml_demo():
    """Run ML models demonstration."""
    print("\n" + "="*70)
    print("MACHINE LEARNING MODELS DEMONSTRATION")
    print("="*70 + "\n")

    print("Testing ML Models:\n")
    print("  1. Rock Classification (Random Forest)")
    print("  2. Sample Value Prediction (Gradient Boosting)")
    print("  3. Anomaly Detection (Isolation Forest)")
    print("  4. Sample Clustering (K-Means)")
    print("  0. Back to Menu\n")

    choice = input("Select model to test: ").strip()

    if choice == "1":
        from ai.ml_models import RockTypeClassifier
        print("\nTesting Rock Classifier...\n")
        classifier = RockTypeClassifier()
        features = [0.15, 0.12, 0.25, 0.85, 0.80]
        rock_type, confidence = classifier.predict(features)
        print(f"Features: [Fe=0.15, Mg=0.12, Si=0.25, Visual=0.85, Spectral=0.80]")
        print(f"Predicted: {rock_type.upper()}")
        print(f"Confidence: {confidence:.1%}\n")

    elif choice == "2":
        from ai.ml_models import SampleValuePredictor
        print("\nTesting Value Predictor...\n")
        predictor = SampleValuePredictor()
        sample = {
            "visual_confidence": 0.90,
            "spectral_confidence": 0.85,
            "rarity": 0.8,
            "accessibility": 0.9,
            "depth": 0.5,
        }
        value = predictor.predict_value(sample)
        print(f"Sample Properties: Visual=90%, Spectral=85%, Rarity=80%, Access=90%, Depth=0.5m")
        print(f"Predicted Value: {value:.2f}/1.00\n")

    elif choice == "3":
        from ai.ml_models import AnomalyDetector
        print("\nTesting Anomaly Detection...\n")
        samples = [
            {"id": i, "visual_confidence": 0.85, "spectral_confidence": 0.80, "confidence": 0.82}
            for i in range(5)
        ]
        samples.append({"id": 5, "visual_confidence": 0.2, "spectral_confidence": 0.15, "confidence": 0.1})
        anomalies = AnomalyDetector.detect_anomalies(samples)
        print(f"Analyzed 6 samples - Found {len(anomalies)} anomalies")
        for a in anomalies:
            print(f"  Sample {a['sample_id']}: {a['reason']}\n")

    elif choice == "4":
        from ai.ml_models import SampleClustering
        print("\nTesting Sample Clustering...\n")
        samples = [
            {"id": i, "composition": {"Fe": 0.15 + i*0.02, "Mg": 0.12, "Si": 0.25, "Al": 0.1}}
            for i in range(10)
        ]
        clusters = SampleClustering.cluster_by_composition(samples, n_clusters=3)
        print(f"Clustered 10 samples into {len(clusters)} groups")
        for cid, csamples in clusters.items():
            ids = [s['id'] for s in csamples]
            print(f"  Cluster {cid}: {ids}\n")

    input("Press ENTER to continue...")


def run_health_demo():
    """Run astronaut health monitoring demonstration."""
    print("\n" + "="*70)
    print("ASTRONAUT HEALTH MONITORING SYSTEM")
    print("="*70 + "\n")

    from ai.health_monitoring import AstronautMonitor, AstronautBiometrics

    # Nominal case
    print("Scenario 1: NOMINAL CONDITIONS")
    print("-" * 70 + "\n")

    monitor = AstronautMonitor()
    biometrics = AstronautBiometrics(
        astronaut_id="EVA-001", timestamp=1000.0, heart_rate=95,
        blood_pressure_sys=125, blood_pressure_dia=80, core_temperature=37.5,
        oxygen_saturation=98, respiration_rate=16, suit_pressure=4.3,
        oxygen_remaining=4.5, co2_level=2.8, suit_integrity=99.5,
        ambient_dust=1.0, suit_temperature=18.0, radiation_exposure=0.10,
        metabolic_rate=300, work_duration=1.0, fatigue_level=0.30,
    )

    health_status, _ = monitor.assess_health_status(biometrics)
    suit_status, _ = monitor.assess_suit_status(biometrics)
    recommendation = monitor.recommend_action(health_status, suit_status, biometrics)

    print(f"Astronaut: {biometrics.astronaut_id}")
    print(f"Health: {health_status.value} | Suit: {suit_status.value}")
    print(f"O₂: {biometrics.oxygen_remaining:.1f}h | HR: {biometrics.heart_rate} bpm")
    print(f"Recommendation: {recommendation['action']}\n")

    # Warning case
    print("Scenario 2: WARNING CONDITIONS")
    print("-" * 70 + "\n")

    biometrics_warn = AstronautBiometrics(
        astronaut_id="EVA-002", timestamp=1000.0, heart_rate=125,
        blood_pressure_sys=150, blood_pressure_dia=95, core_temperature=38.5,
        oxygen_saturation=93, respiration_rate=22, suit_pressure=3.9,
        oxygen_remaining=1.2, co2_level=4.5, suit_integrity=92.0,
        ambient_dust=6.0, suit_temperature=20.5, radiation_exposure=0.35,
        metabolic_rate=450, work_duration=3.5, fatigue_level=0.75,
    )

    health_status, h_alerts = monitor.assess_health_status(biometrics_warn)
    suit_status, s_alerts = monitor.assess_suit_status(biometrics_warn)
    recommendation = monitor.recommend_action(health_status, suit_status, biometrics_warn)

    print(f"Astronaut: {biometrics_warn.astronaut_id}")
    print(f"Health: {health_status.value} | Suit: {suit_status.value}")
    print(f"O₂: {biometrics_warn.oxygen_remaining:.1f}h | HR: {biometrics_warn.heart_rate} bpm")
    print(f"Recommendation: {recommendation['action']}")
    print(f"Reason: {recommendation['reason']}\n")

    print("Alerts:")
    for alert in h_alerts + s_alerts:
        print(f"  WARNING: {alert}")

    print("\nScenario 3: SPACE CONDITIONS HEART RATE PREDICTION")
    print("-" * 70 + "\n")

    space_prediction = monitor.predict_heart_rate_from_conditions(
        baseline_heart_rate=72,
        conditions={
            "radiation_usv_h": 145.0,
            "temperature_c": -175.0,
            "suit_pressure": 3.6,
            "oxygen_saturation": 92,
            "co2_level": 4.8,
            "dust_level": 7.5,
            "metabolic_rate": 380,
            "fatigue_level": 0.78,
            "work_duration": 3.8,
        },
    )

    print(f"Predicted HR: {space_prediction['predicted_heart_rate']} bpm")
    print(f"Status: {space_prediction['heart_rate_status'].upper()}")
    print(f"Recommendation: {space_prediction['recommendation']}")
    if space_prediction["warning_signs"]:
        print("Warning Signs:")
        for warning in space_prediction["warning_signs"]:
            print(f"  - {warning}")

    input("\nPress ENTER to continue...")


def interactive_mode():
    """Run interactive menu mode."""
    while True:
        clear_screen()
        print_banner()
        print_main_menu()

        choice = input("Enter your choice (1-6): ").strip()

        if choice == "1":
            clear_screen()
            print_banner()
            print_dataset_menu()
            input("Press ENTER to return...")

        elif choice == "2":
            clear_screen()
            print_banner()
            datasets = print_dataset_menu()
            dataset_choice = input("Select dataset (0-5): ").strip()

            if dataset_choice not in datasets:
                continue

            dataset_key = datasets[dataset_choice]["key"]

            clear_screen()
            print_banner()
            missions = print_mission_menu()
            mission_choice = input("Select mission (0-3): ").strip()

            if mission_choice not in missions:
                continue

            mission_key = missions[mission_choice]["key"]

            clear_screen()
            print_banner()
            print_llm_menu()
            llm_choice = input("Select option (0-2): ").strip()

            use_llm = llm_choice == "1"

            if llm_choice in ["1", "2"]:
                run_mission(dataset_key, mission_key, use_llm)

        elif choice == "3":
            clear_screen()
            print_banner()
            print("\nMission reports are generated after each mission.\n")
            input("Press ENTER to return...")

        elif choice == "4":
            clear_screen()
            print_banner()
            run_ml_demo()

        elif choice == "5":
            clear_screen()
            print_banner()
            run_health_demo()

        elif choice == "6":
            clear_screen()
            print("Goodbye!")
            sys.exit(0)


class MissionControl:
    """Main mission control system."""

    def __init__(self, llm_client=None, model: str = "claude-opus"):
        """Initialize mission control."""
        self.rover = Rover()
        self.camera = Camera()
        self.depth_sensor = DepthSensor()
        self.thermal_sensor = ThermalSensor()
        self.spectral_analyzer = SpectralAnalyzer()
        self.rock_detector = RockDetector()
        self.rock_classifier = RockClassifier()
        self.sensor_fusion = SensorFusion()
        self.scientist = Scientist(llm_client=llm_client, model=model)
        self.route_planner = RoutePlanner()
        self.mission_log = []
        self.terrain_map = {}

    def execute_exploration_mission(
        self, num_locations: int = 5, terrain_type: str = "simple",
        use_llm: bool = False, generate_report: bool = True, dataset: dict = None,
    ):
        """Execute autonomous exploration mission."""
        print(f"\n{'='*60}\nAUTONOMOUS EXPLORATION MISSION INITIATED\n{'='*60}\n")
        samples_found = []
        locations = dataset["locations"] if dataset else None

        for location_idx in range(num_locations):
            if not self.rover.is_operational():
                print(f"WARNING:️  Mission halted: Low battery ({self.rover.battery:.1f}%)")
                break

            print(f"\n📍 Exploring Location {location_idx + 1}/{num_locations}")
            print("-" * 40)

            location_data = locations[location_idx] if locations and location_idx < len(locations) else None
            sensor_data = self._sense(location_idx, location_data)
            print(f"✓ Sensors active: Camera, Depth, Thermal, Spectral")

            world_model = self.sensor_fusion.fuse(sensor_data)
            print(f"✓ Fused {len(world_model['rocks'])} rock detections")

            if world_model["rocks"]:
                location_samples = self._analyze_rocks(world_model["rocks"], use_llm=use_llm)
                samples_found.extend(location_samples)
                print(f"✓ Analyzed {len(location_samples)} samples")

            next_location = self._plan_movement(location_idx, num_locations)
            print(f"✓ Next waypoint: {next_location}")

            self.rover.move_to(next_location, step_size=0.2)
            print(f"✓ Rover position: {self.rover.get_state()['position']}")

        if generate_report and samples_found:
            self._generate_report(samples_found)

        print(f"\n{'='*60}\nMISSION COMPLETE\n{'='*60}\n")

    def _sense(self, location_idx: int, location_data: dict = None) -> dict:
        """Capture sensor data or use dataset."""
        if location_data:
            rocks = location_data.get("rocks", [])
            thermal_anomalies = location_data.get("hazards", [])
            spectral = self.spectral_analyzer.analyze({})
        else:
            rocks = self.rock_detector.detect(np.random.randn(480, 640, 3))
            spectral = self.spectral_analyzer.analyze({})
            thermal_anomalies = self.thermal_sensor.detect_anomalies()

        return {
            "location": location_idx,
            "rocks": rocks,
            "spectral": spectral,
            "thermal_anomalies": thermal_anomalies,
            "depth": {"value": 5.0 + np.random.randn() * 1.0},
            "timestamp": location_idx,
            "location_data": location_data,
        }

    def _analyze_rocks(self, rocks: list, use_llm: bool = False) -> list:
        """Analyze detected rocks."""
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
            spectral = self.spectral_analyzer.analyze({})
            sample["spectral_confidence"] = spectral.get("confidence", 0.7)
            analysis = self.scientist.analyze_sample(sample)
            analyzed_samples.append(analysis)

        return analyzed_samples

    def _plan_movement(self, current_idx: int, total_locations: int) -> tuple:
        """Plan next waypoint."""
        if current_idx + 1 < total_locations:
            return (current_idx + 2.0, 0.0)
        else:
            return self.rover.position

    def _generate_report(self, samples: list):
        """Generate mission report."""
        print(f"\n{'='*60}\nSCIENCE REPORT\n{'='*60}\n")
        ranked = self.scientist.rank_samples(samples)

        print(f"Mission Summary:")
        print(f"  Samples Analyzed: {len(samples)}")
        print(f"  Battery Remaining: {self.rover.battery:.1f}%")
        print(f"  Samples Collected: {len(self.rover.samples_collected)}")

        print(f"\nTop 5 Scientifically Valuable Samples:\n")
        for i, sample in enumerate(ranked[:5], 1):
            print(f"{i}. Sample #{sample['sample_id']} ({sample['rock_type'].upper()})")
            print(f"   Scientific Value: {sample['scientific_value']:.2f}")
            if "explanation" in sample:
                print(f"   Notes: {sample['explanation'][:100]}...")
            print()

        print(f"Recommendations:")
        print(f"  - Prioritize high-value olivine and anorthosite samples")
        print(f"  - Return to base when battery < 10%")
        print(f"  - Next mission: explore southern plateau")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Autonomous Rover Mission Control")
    parser.add_argument("--dataset", default=None, help="Dataset to use")
    parser.add_argument("--mission", default="explore", help="Mission type")
    parser.add_argument("--use-llm", action="store_true", help="Enable LLM")
    parser.add_argument("--generate-report", action="store_true", default=True, help="Generate report")
    parser.add_argument("--list-datasets", action="store_true", help="List datasets")

    args, unknown = parser.parse_known_args()

    # If no arguments provided, launch interactive mode
    if not args.dataset and not args.list_datasets and not unknown:
        interactive_mode()
        return

    # List datasets
    if args.list_datasets:
        from data.datasets import DatasetLoader
        print("\nAvailable Datasets:\n")
        for name, desc in DatasetLoader.get_dataset_info().items():
            print(f"  {name:12} - {desc}")
        print()
        return

    # Load dataset
    from data.datasets import DatasetLoader
    try:
        dataset = DatasetLoader.load_dataset(args.dataset)
        print(f"✓ Loaded dataset: {dataset['name']}\n")
    except ValueError as e:
        print(f"✗ Error: {e}\n")
        return

    # Initialize mission
    llm_client = None
    if args.use_llm:
        try:
            from anthropic import Anthropic
            llm_client = Anthropic()
            print("✓ LLM integration enabled (Claude)\n")
        except ImportError:
            print("WARNING:️  Anthropic SDK not available. Running without LLM.\n")

    mission = MissionControl(llm_client=llm_client)
    num_locations = dataset.get("num_locations", 5)
    mission.execute_exploration_mission(
        num_locations=num_locations,
        use_llm=args.use_llm,
        generate_report=args.generate_report,
        dataset=dataset,
    )


if __name__ == "__main__":
    main()
