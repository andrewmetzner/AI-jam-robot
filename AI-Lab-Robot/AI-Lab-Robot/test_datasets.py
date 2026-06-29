#!/usr/bin/env python3
"""
Test script to demonstrate mission execution with different mock datasets.
Run various mission profiles and evaluate performance.
"""

import subprocess
import sys


def run_mission(dataset: str, mission: str = "explore", use_llm: bool = False, show_report: bool = True):
    """Run a mission with specified dataset."""
    print(f"\n{'='*70}")
    print(f"Running Mission: {mission.upper()} | Dataset: {dataset.upper()}")
    print(f"{'='*70}\n")

    cmd = [
        sys.executable,
        "main.py",
        "--mission", mission,
        "--dataset", dataset,
    ]

    if use_llm:
        cmd.append("--use-llm")

    if show_report:
        cmd.append("--generate-report")

    result = subprocess.run(cmd, cwd="AI-Lab-Robot")
    return result.returncode == 0


def list_datasets():
    """Display available datasets."""
    print("\n" + "="*70)
    print("AVAILABLE MOCK DATASETS FOR TESTING")
    print("="*70 + "\n")

    cmd = [sys.executable, "main.py", "--list-datasets"]
    subprocess.run(cmd, cwd="AI-Lab-Robot")


def test_all_datasets():
    """Run all datasets sequentially."""
    datasets = ["simple", "complex", "crater", "hazard", "drill"]

    print("\n" + "="*70)
    print("TESTING ALL DATASETS")
    print("="*70)

    results = {}
    for dataset in datasets:
        success = run_mission(dataset, mission="explore", show_report=True)
        results[dataset] = "✓ PASS" if success else "✗ FAIL"

    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70 + "\n")

    for dataset, result in results.items():
        print(f"  {dataset:12} {result}")

    print()


def test_dataset_features():
    """Test specific dataset features."""
    print("\n" + "="*70)
    print("TESTING DATASET-SPECIFIC FEATURES")
    print("="*70 + "\n")

    # Test 1: Simple dataset
    print("\n1. Simple Dataset (Easy Terrain)")
    run_mission("simple", mission="explore", show_report=True)

    # Test 2: Complex terrain
    print("\n2. Complex Terrain (Navigation Challenge)")
    run_mission("complex", mission="explore", show_report=True)

    # Test 3: Crater exploration with coring
    print("\n3. Crater Exploration (Subsurface Access)")
    run_mission("crater", mission="explore", show_report=True)

    # Test 4: Hazard assessment
    print("\n4. Hazardous Zone (Risk Assessment)")
    run_mission("hazard", mission="explore", show_report=True)

    # Test 5: Drill site survey
    print("\n5. Deep Drilling Sites (Subsurface Science)")
    run_mission("drill", mission="explore", show_report=True)


def main():
    """Main test runner."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "list":
            list_datasets()
        elif command == "all":
            test_all_datasets()
        elif command == "features":
            test_dataset_features()
        elif command == "simple":
            run_mission("simple", mission="explore", show_report=True)
        elif command == "complex":
            run_mission("complex", mission="explore", show_report=True)
        elif command == "crater":
            run_mission("crater", mission="explore", show_report=True)
        elif command == "hazard":
            run_mission("hazard", mission="explore", show_report=True)
        elif command == "drill":
            run_mission("drill", mission="explore", show_report=True)
        else:
            print(f"Unknown command: {command}")
            print_help()
    else:
        print_help()


def print_help():
    """Print help message."""
    print("""
USAGE:  python test_datasets.py [COMMAND]

COMMANDS:
  list              List all available datasets
  all               Run all datasets (default mission: explore)
  features          Test dataset-specific features
  simple            Run simple dataset
  complex           Run complex terrain dataset
  crater            Run crater exploration dataset
  hazard            Run hazardous zone dataset
  drill             Run deep drilling sites dataset

EXAMPLES:
  python test_datasets.py list
  python test_datasets.py simple
  python test_datasets.py all

Or run main.py directly:
  cd AI-Lab-Robot
  python main.py --list-datasets
  python main.py --dataset simple --mission explore
  python main.py --dataset crater --mission explore --generate-report
  python main.py --dataset hazard --mission explore --use-llm
    """)


if __name__ == "__main__":
    main()
