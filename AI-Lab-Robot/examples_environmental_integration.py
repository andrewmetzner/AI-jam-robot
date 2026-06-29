#!/usr/bin/env python3
"""
Example: Integrating Environmental Sensor Analysis with Rover Systems

Demonstrates how to use scikit-learn environmental monitoring with rover
decision-making, sample prioritization, and mission planning.
"""

from ai.environmental_analysis import (
    EnvironmentalSensorData,
    EnvironmentalMonitor,
    SensorDataGenerator,
    EnvironmentalLocationRanker,
    SensorClusterAnalysis,
)
from ai.fusion.environmental_fusion import (
    EnvironmentalFusionEngine,
    SampleContextAnalyzer,
    CriticalEventDetector,
)
import numpy as np


def example_1_real_time_monitoring():
    """Example 1: Real-time environmental monitoring at a location."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Real-Time Environmental Monitoring")
    print("="*70 + "\n")

    monitor = EnvironmentalMonitor()

    # Simulate sensor readings from a lunar location
    sensor_data = EnvironmentalSensorData(location_id="LOC-001", timestamp=1000.0)
    sensor_data.temperature_c = 45.0  # Moderate temperature
    sensor_data.humidity_percent = 15.0
    sensor_data.pressure_pa = 101325
    sensor_data.air_quality_absorbance = 0.25
    sensor_data.air_quality_scattering = 0.30
    sensor_data.cosmic_radiation_mrem = 35.0  # Moderate radiation
    sensor_data.ec_conductivity_us_cm = 2500

    # Assess environment
    assessment = monitor.assess_environment(sensor_data)

    print(f"Location: {assessment['location_id']}")
    print(f"Temperature: {sensor_data.temperature_c}°C")
    print(f"Humidity: {sensor_data.humidity_percent}%")
    print(f"Radiation: {sensor_data.cosmic_radiation_mrem} mrem/h")
    print(f"\nAssessment:")
    print(f"  Safe: {assessment['is_safe']}")
    print(f"  Hazard Probability: {assessment['hazard_probability']:.2%}")
    print(f"  Anomaly Detected: {assessment['anomaly_detected']}")
    print(f"\nRecommendations:")
    for rec in assessment['recommendations']:
        print(f"  - {rec}")


def example_2_environmental_risk_routing():
    """Example 2: Route planning based on environmental hazards."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Environmental Risk-Based Route Planning")
    print("="*70 + "\n")

    fusion = EnvironmentalFusionEngine()

    # Define waypoints with environmental conditions
    waypoints = [
        {
            "id": "WP-1",
            "x": 0, "y": 0,
            "temperature_c": 20,
            "humidity_percent": 50,
            "pressure_pa": 101325,
            "air_quality_absorbance": 0.2,
            "air_quality_scattering": 0.2,
            "cosmic_radiation_mrem": 15,
            "ec_conductivity_us_cm": 1000,
            "terrain_slope": 2,
        },
        {
            "id": "WP-2",
            "x": 50, "y": 50,
            "temperature_c": 95,  # Hot
            "humidity_percent": 25,
            "pressure_pa": 101325,
            "air_quality_absorbance": 0.5,
            "air_quality_scattering": 0.5,
            "cosmic_radiation_mrem": 60,  # High radiation
            "ec_conductivity_us_cm": 3500,
            "terrain_slope": 8,
        },
        {
            "id": "WP-3",
            "x": 100, "y": 100,
            "temperature_c": 35,
            "humidity_percent": 40,
            "pressure_pa": 101325,
            "air_quality_absorbance": 0.3,
            "air_quality_scattering": 0.3,
            "cosmic_radiation_mrem": 25,
            "ec_conductivity_us_cm": 2000,
            "terrain_slope": 3,
        },
    ]

    # Create hazard map
    print("Creating environmental hazard map...")
    hazard_map = fusion.create_hazard_map(waypoints)

    print("\nWaypoint Risk Assessment:")
    for wp_id, hazard_info in hazard_map.items():
        risk = hazard_info["risk"]
        print(f"\n  {wp_id}:")
        print(f"    Risk Level: {risk['risk_level']} ({risk['risk_score']:.1%})")
        print(f"    Action: {risk['recommended_action']}")
        print(f"    Max Speed: {risk['max_speed_percent']}%")

    # Identify safe zones
    print("\nIdentifying safe zones...")
    safe_zones = fusion.identify_safe_zones(waypoints, safety_threshold=0.4)
    print(f"Safe zones: {safe_zones}")

    # Recommended route
    print("\nRecommended route planning:")
    print("  Route 1 (Safest): WP-1 -> WP-3 -> Destination")
    print("  Route 2 (Direct): WP-1 -> WP-2 -> Destination (HIGH RISK)")
    print("  Recommendation: Use Route 1 (Safest)")


def example_3_sample_prioritization():
    """Example 3: Prioritize samples based on environmental context."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Sample Prioritization in Environmental Context")
    print("="*70 + "\n")

    analyzer = SampleContextAnalyzer()

    # Define samples at different locations
    samples = [
        {
            "id": "SAMPLE-A",
            "base_value": 0.8,
            "location": "LOC-SAFE",
            "temperature_c": 25,
            "humidity_percent": 50,
            "cosmic_radiation_mrem": 15,
        },
        {
            "id": "SAMPLE-B",
            "base_value": 0.7,
            "location": "LOC-HAZARD",
            "temperature_c": 110,
            "humidity_percent": 20,
            "cosmic_radiation_mrem": 85,
        },
        {
            "id": "SAMPLE-C",
            "base_value": 0.75,
            "location": "LOC-MODERATE",
            "temperature_c": 55,
            "humidity_percent": 45,
            "cosmic_radiation_mrem": 35,
        },
    ]

    print("Sample Analysis with Environmental Context:")
    for sample in samples:
        assessment = analyzer.assess_sample_value_in_context(
            sample=sample,
            environmental_conditions={
                "temperature_c": sample["temperature_c"],
                "humidity_percent": sample["humidity_percent"],
                "cosmic_radiation_mrem": sample["cosmic_radiation_mrem"],
                "air_quality_absorbance": 0.3,
                "air_quality_scattering": 0.3,
                "pressure_pa": 101325,
                "ec_conductivity_us_cm": 1500,
            }
        )

        print(f"\n  {assessment['sample_id']}:")
        print(f"    Base Value: {assessment['base_value']:.2f}")
        print(f"    Environmental Adjustment: {assessment['context_adjustment']:.2f}")
        print(f"    Adjusted Value: {assessment['adjusted_value']:.2f}")
        print(f"    Collection Strategy: {assessment['collection_strategy']}")


def example_4_critical_event_detection():
    """Example 4: Detect critical environmental events."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Critical Event Detection")
    print("="*70 + "\n")

    # Normal conditions
    print("Scenario 1: Normal Conditions")
    events = CriticalEventDetector.check_all_critical_conditions(
        temperature=45.0,
        radiation=20.0,
        air_quality_abs=0.3,
        air_quality_scat=0.3,
        pressure=101325,
    )
    print(f"  Events: {events['critical_events'] if events['critical_events'] else 'None'}")
    print(f"  Action: {events['action']}\n")

    # Hazardous conditions
    print("Scenario 2: Multiple Hazards Detected")
    events = CriticalEventDetector.check_all_critical_conditions(
        temperature=140.0,  # Extreme heat
        radiation=110.0,  # Extreme radiation
        air_quality_abs=0.85,  # Poor air quality
        air_quality_scat=0.85,
        pressure=80000,  # Low pressure
    )
    print(f"  Events: {events['critical_events']}")
    print(f"  Action: {events['action']}\n")


def example_5_location_clustering():
    """Example 5: Cluster locations by environmental similarity."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Location Clustering by Environmental Type")
    print("="*70 + "\n")

    # Generate diverse locations
    locations = SensorDataGenerator.generate_dataset(n_locations=6, n_samples_per_location=1)

    location_data = []
    for sensor in locations:
        location_data.append({
            "id": sensor.location_id,
            "temperature_c": sensor.temperature_c,
            "humidity_percent": sensor.humidity_percent,
            "pressure_pa": sensor.pressure_pa,
            "air_quality_absorbance": sensor.air_quality_absorbance,
            "air_quality_scattering": sensor.air_quality_scattering,
            "cosmic_radiation_mrem": sensor.cosmic_radiation_mrem,
            "ec_conductivity_us_cm": sensor.ec_conductivity_us_cm,
        })

    # Cluster by environmental conditions
    clusters = SensorClusterAnalysis.cluster_by_environment(location_data, n_clusters=3)

    print("Environmental Clusters:")
    for cluster_id, cluster_locs in clusters.items():
        print(f"\n  Cluster {cluster_id}:")
        for loc in cluster_locs:
            print(f"    - {loc['id']} (Temp: {loc['temperature_c']:.1f}°C, Rad: {loc['cosmic_radiation_mrem']:.1f} mrem/h)")


def example_6_location_ranking():
    """Example 6: Rank locations by environmental suitability."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Ranking Locations by Suitability")
    print("="*70 + "\n")

    location_data = [
        {
            "id": "SITE-ALPHA",
            "temperature_c": 25,
            "humidity_percent": 50,
            "pressure_pa": 101325,
            "air_quality_absorbance": 0.2,
            "air_quality_scattering": 0.2,
            "cosmic_radiation_mrem": 18,
            "ec_conductivity_us_cm": 1200,
        },
        {
            "id": "SITE-BETA",
            "temperature_c": 95,
            "humidity_percent": 25,
            "pressure_pa": 101325,
            "air_quality_absorbance": 0.6,
            "air_quality_scattering": 0.6,
            "cosmic_radiation_mrem": 75,
            "ec_conductivity_us_cm": 4000,
        },
        {
            "id": "SITE-GAMMA",
            "temperature_c": 50,
            "humidity_percent": 45,
            "pressure_pa": 101325,
            "air_quality_absorbance": 0.35,
            "air_quality_scattering": 0.35,
            "cosmic_radiation_mrem": 30,
            "ec_conductivity_us_cm": 2000,
        },
    ]

    ranker = EnvironmentalLocationRanker()
    ranked = ranker.rank_locations(location_data)

    print("Environmental Suitability Ranking:")
    for i, loc in enumerate(ranked, 1):
        print(f"\n  {i}. {loc['location_id']}")
        print(f"     Suitability Score: {loc['environmental_suitability']:.2%}")
        print(f"     Temperature: {loc['sensor_data']['temperature_c']:.1f}°C")
        print(f"     Radiation: {loc['sensor_data']['cosmic_radiation_mrem']:.1f} mrem/h")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("ENVIRONMENTAL SENSOR INTEGRATION EXAMPLES")
    print("Using Scikit-Learn for Robotics Data Analysis")
    print("="*70)

    example_1_real_time_monitoring()
    example_2_environmental_risk_routing()
    example_3_sample_prioritization()
    example_4_critical_event_detection()
    example_5_location_clustering()
    example_6_location_ranking()

    print("\n" + "="*70)
    print("All examples completed successfully!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
