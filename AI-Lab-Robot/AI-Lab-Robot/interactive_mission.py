#!/usr/bin/env python3
"""
Interactive Mission Control for Autonomous Rover
Simple menu-driven interface for mission planning and execution.
"""

import sys
import os
from pathlib import Path


def clear_screen():
    """Clear terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    """Print welcome banner."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                    AUTONOMOUS ROVER MISSION CONTROL                        ║
║                       2040s Lunar Research Station                         ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
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


def print_options_menu():
    """Print mission options menu."""
    print("\n" + "="*70)
    print("MISSION OPTIONS")
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

        # Test sample
        features = [0.15, 0.12, 0.25, 0.85, 0.80]  # Fe, Mg, Si, vis_conf, spec_conf
        rock_type, confidence = classifier.predict(features)

        print(f"Features: [Fe=0.15, Mg=0.12, Si=0.25, Visual_Conf=0.85, Spectral_Conf=0.80]")
        print(f"Predicted Rock Type: {rock_type.upper()}")
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
        print(f"Sample Properties:")
        print(f"  Visual Confidence: 90%")
        print(f"  Spectral Confidence: 85%")
        print(f"  Rarity: 80% (rare)")
        print(f"  Accessibility: 90% (easy to reach)")
        print(f"  Depth: 0.5 meters")
        print(f"\nPredicted Scientific Value: {value:.2f}/1.00\n")

    elif choice == "3":
        from ai.ml_models import AnomalyDetector
        print("\nTesting Anomaly Detection...\n")

        samples = [
            {"id": i, "visual_confidence": 0.85, "spectral_confidence": 0.80, "confidence": 0.82}
            for i in range(5)
        ]
        # Add anomalous sample
        samples.append({"id": 5, "visual_confidence": 0.2, "spectral_confidence": 0.15, "confidence": 0.1})

        anomalies = AnomalyDetector.detect_anomalies(samples)

        print(f"Analyzed 6 samples")
        print(f"Detected {len(anomalies)} anomalies:\n")

        for anomaly in anomalies:
            print(f"  Sample {anomaly['sample_id']}: {anomaly['reason']}")
            print(f"    Anomaly Score: {anomaly['anomaly_score']:.2f}\n")

    elif choice == "4":
        from ai.ml_models import SampleClustering
        print("\nTesting Sample Clustering...\n")

        samples = [
            {"id": i, "composition": {"Fe": 0.15 + i*0.02, "Mg": 0.12, "Si": 0.25, "Al": 0.1}}
            for i in range(10)
        ]

        clusters = SampleClustering.cluster_by_composition(samples, n_clusters=3)

        print(f"Clustered 10 samples into {len(clusters)} composition groups:\n")

        for cluster_id, cluster_samples in clusters.items():
            print(f"  Cluster {cluster_id}: {len(cluster_samples)} samples")
            sample_ids = [s['id'] for s in cluster_samples]
            print(f"    Sample IDs: {sample_ids}\n")

    input("Press ENTER to continue...")


def run_health_demo():
    """Run astronaut health monitoring demonstration."""
    print("\n" + "="*70)
    print("ASTRONAUT HEALTH MONITORING SYSTEM")
    print("="*70 + "\n")

    from ai.health_monitoring import AstronautMonitor, AstronautBiometrics, SuitEnvironmentMonitor

    # Create nominal case
    print("Scenario 1: NOMINAL CONDITIONS")
    print("-" * 70 + "\n")

    monitor = AstronautMonitor()
    biometrics = AstronautBiometrics(
        astronaut_id="EVA-001",
        timestamp=1000.0,
        heart_rate=95,
        blood_pressure_sys=125,
        blood_pressure_dia=80,
        core_temperature=37.5,
        oxygen_saturation=98,
        respiration_rate=16,
        suit_pressure=4.3,
        oxygen_remaining=4.5,
        co2_level=2.8,
        suit_integrity=99.5,
        ambient_dust=1.0,
        suit_temperature=18.0,
        radiation_exposure=0.10,
        metabolic_rate=300,
        work_duration=1.0,
        fatigue_level=0.30,
    )

    health_status, health_alerts = monitor.assess_health_status(biometrics)
    suit_status, suit_alerts = monitor.assess_suit_status(biometrics)
    recommendation = monitor.recommend_action(health_status, suit_status, biometrics)

    print(f"Astronaut: {biometrics.astronaut_id}")
    print(f"Health Status: {health_status.value}")
    print(f"Suit Status: {suit_status.value}")
    print(f"Recommendation: {recommendation['action']}")
    print(f"Oxygen Remaining: {biometrics.oxygen_remaining:.1f} hours\n")

    # Create warning case
    print("Scenario 2: WARNING CONDITIONS")
    print("-" * 70 + "\n")

    biometrics_warn = AstronautBiometrics(
        astronaut_id="EVA-002",
        timestamp=1000.0,
        heart_rate=125,
        blood_pressure_sys=150,
        blood_pressure_dia=95,
        core_temperature=38.5,
        oxygen_saturation=93,
        respiration_rate=22,
        suit_pressure=3.9,
        oxygen_remaining=1.2,
        co2_level=4.5,
        suit_integrity=92.0,
        ambient_dust=6.0,
        suit_temperature=20.5,
        radiation_exposure=0.35,
        metabolic_rate=450,
        work_duration=3.5,
        fatigue_level=0.75,
    )

    health_status, health_alerts = monitor.assess_health_status(biometrics_warn)
    suit_status, suit_alerts = monitor.assess_suit_status(biometrics_warn)
    recommendation = monitor.recommend_action(health_status, suit_status, biometrics_warn)

    print(f"Astronaut: {biometrics_warn.astronaut_id}")
    print(f"Health Status: {health_status.value}")
    print(f"Suit Status: {suit_status.value}")
    print(f"Recommendation: {recommendation['action']}")
    print(f"Reason: {recommendation['reason']}")
    print(f"Oxygen Remaining: {biometrics_warn.oxygen_remaining:.1f} hours")
    print(f"Estimated Return Time: {recommendation['estimated_time_to_base']:.1f} hours\n")

    print("\nAlerts:")
    for alert in health_alerts + suit_alerts:
        print(f"  ⚠ {alert}")

    input("\nPress ENTER to continue...")


def main_menu_loop():
    """Main menu loop."""
    while True:
        clear_screen()
        print_banner()
        print_main_menu()

        choice = input("Enter your choice (1-6): ").strip()

        if choice == "1":
            # View datasets
            clear_screen()
            print_banner()
            datasets = print_dataset_menu()
            input("Press ENTER to return to main menu...")

        elif choice == "2":
            # Run mission
            clear_screen()
            print_banner()
            datasets = print_dataset_menu()
            dataset_choice = input("Select dataset (0-5): ").strip()

            if dataset_choice == "0":
                continue

            if dataset_choice not in datasets:
                print("Invalid choice")
                input("Press ENTER to continue...")
                continue

            dataset_key = datasets[dataset_choice]["key"]

            clear_screen()
            print_banner()
            missions = print_mission_menu()
            mission_choice = input("Select mission (0-3): ").strip()

            if mission_choice == "0":
                continue

            if mission_choice not in missions:
                print("Invalid choice")
                input("Press ENTER to continue...")
                continue

            mission_key = missions[mission_choice]["key"]

            clear_screen()
            print_banner()
            print_options_menu()
            options_choice = input("Select option (0-2): ").strip()

            use_llm = options_choice == "1"

            if options_choice in ["1", "2"]:
                run_mission(dataset_key, mission_key, use_llm)

        elif choice == "3":
            # View reports
            clear_screen()
            print_banner()
            print("\nMission reports are generated after each mission.")
            print("Look for SCIENCE REPORT output above.\n")
            input("Press ENTER to return to main menu...")

        elif choice == "4":
            # ML demo
            clear_screen()
            print_banner()
            run_ml_demo()

        elif choice == "5":
            # Health monitoring
            clear_screen()
            print_banner()
            run_health_demo()

        elif choice == "6":
            clear_screen()
            print("Goodbye!")
            sys.exit(0)

        else:
            print("Invalid choice. Please try again.")
            input("Press ENTER to continue...")


if __name__ == "__main__":
    main_menu_loop()
