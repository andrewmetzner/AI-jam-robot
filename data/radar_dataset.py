"""Convert radar observations into rover mission dataset format."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
from data.radar_loader import RadarDatasetLoader


class RadarMissionDataset:
    """Convert real radar mock data into rover mission locations."""

    @staticmethod
    def load_radar_mission(filepath: str = None) -> Dict:
        """
        Load radar data and convert to mission format.

        Returns mission dict with locations derived from radar tracks.
        """
        loader = RadarDatasetLoader()
        df = loader.load_radar_data(filepath)

        if df is None:
            return None

        # Group by track_id to create mission locations
        locations = []
        for track_id, group in df.groupby('track_id'):
            # Get most frequent/confident observation for this track
            best_obs = group.loc[group['confidence'].idxmax()]

            location = {
                "id": int(track_id),
                "name": f"Track-{track_id}",
                "position": (float(best_obs['range_m']), float(best_obs['azimuth_deg'])),
                "rocks": [
                    {
                        "id": int(track_id),
                        "visual_features": {"conf": float(best_obs['confidence'])},
                        "type": best_obs['object_class'],
                        "position": (float(best_obs['range_m']), float(best_obs['azimuth_deg'])),
                    }
                ],
                "hazards": [],
                "metadata": {
                    "object_class": best_obs['object_class'],
                    "elevation": float(best_obs['elevation_deg']),
                    "rcs": float(best_obs['rcs_dbsm']),
                    "snr": float(best_obs['snr_db']),
                    "confidence": float(best_obs['confidence']),
                    "observations": len(group),
                }
            }
            locations.append(location)

        # Limit to top tracks by confidence for mission
        locations.sort(key=lambda x: x['metadata']['confidence'], reverse=True)
        locations = locations[:10]  # Top 10 tracks

        mission = {
            "name": "Radar Survey Mission",
            "description": "Autonomous exploration based on radar track observations",
            "num_locations": len(locations),
            "locations": locations,
            "total_observations": len(df),
            "source": "mock_radar_observations_1hour.csv",
            "metadata": {
                "start_time": df['timestamp'].min(),
                "end_time": df['timestamp'].max(),
                "unique_tracks": df['track_id'].nunique(),
                "object_classes": df['object_class'].unique().tolist(),
            }
        }

        return mission

    @staticmethod
    def get_radar_statistics(filepath: str = None) -> Dict:
        """Get summary statistics of radar dataset."""
        loader = RadarDatasetLoader()
        df = loader.load_radar_data(filepath)

        if df is None:
            return {}

        return {
            "total_observations": len(df),
            "unique_tracks": df['track_id'].nunique(),
            "time_range": f"{df['timestamp'].min()} to {df['timestamp'].max()}",
            "object_classes": df['object_class'].value_counts().to_dict(),
            "range_stats": {
                "min": float(df['range_m'].min()),
                "max": float(df['range_m'].max()),
                "mean": float(df['range_m'].mean()),
            },
            "confidence_stats": {
                "min": float(df['confidence'].min()),
                "max": float(df['confidence'].max()),
                "mean": float(df['confidence'].mean()),
            }
        }

    @staticmethod
    def filter_by_class(df: pd.DataFrame, object_class: str) -> Dict:
        """Create mission from specific object class."""
        mission_df = df[df['object_class'] == object_class]

        locations = []
        for track_id, group in mission_df.groupby('track_id'):
            best_obs = group.loc[group['confidence'].idxmax()]
            location = {
                "id": int(track_id),
                "name": f"{object_class}-{track_id}",
                "position": (float(best_obs['range_m']), float(best_obs['azimuth_deg'])),
                "rocks": [{
                    "id": int(track_id),
                    "type": object_class,
                    "position": (float(best_obs['range_m']), float(best_obs['azimuth_deg'])),
                    "confidence": float(best_obs['confidence']),
                }],
                "hazards": [],
            }
            locations.append(location)

        return {
            "name": f"Radar Survey - {object_class}",
            "description": f"Exploration targets from {object_class} detections",
            "num_locations": len(locations),
            "locations": locations,
            "metadata": {"object_class": object_class}
        }


def demonstrate_radar_dataset():
    """Show radar dataset capabilities."""
    print("\n" + "="*70)
    print("RADAR MOCK DATASET INTEGRATION")
    print("="*70 + "\n")

    # Load statistics
    stats = RadarMissionDataset.get_radar_statistics()

    print("Dataset Statistics:")
    print(f"  Total Observations: {stats['total_observations']:,}")
    print(f"  Unique Tracks: {stats['unique_tracks']}")
    print(f"  Time Range: {stats['time_range']}")
    print(f"\nObject Classes:")
    for obj_class, count in stats['object_classes'].items():
        pct = (count / stats['total_observations']) * 100
        print(f"  - {obj_class:12} {count:6,} observations ({pct:5.1f}%)")

    print(f"\nRange Statistics (meters):")
    print(f"  Min:  {stats['range_stats']['min']:8.1f}")
    print(f"  Max:  {stats['range_stats']['max']:8.1f}")
    print(f"  Mean: {stats['range_stats']['mean']:8.1f}")

    # Load as mission
    print(f"\n" + "-"*70)
    print("Converting to Mission Format...")
    mission = RadarMissionDataset.load_radar_mission()

    print(f"Mission: {mission['name']}")
    print(f"Locations: {mission['num_locations']}")
    print(f"Source: {mission['source']}")

    print(f"\nTop 3 Locations:")
    for i, loc in enumerate(mission['locations'][:3], 1):
        print(f"  {i}. {loc['name']}")
        print(f"     Class: {loc['metadata']['object_class']}")
        print(f"     Confidence: {loc['metadata']['confidence']:.2f}")
        print(f"     Range: {loc['metadata']['rcs']:.1f} dBsm")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    demonstrate_radar_dataset()
