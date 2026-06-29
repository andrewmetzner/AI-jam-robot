"""Loader for real mock radar observation data."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List


class RadarDatasetLoader:
    """Load real mock radar observations from CSV."""

    @staticmethod
    def load_radar_data(filepath: str = None) -> pd.DataFrame:
        """Load radar observations from CSV file."""
        if filepath is None:
            filepath = Path(__file__).parent.parent / "datasets" / "mock_radar_observations_1hour.csv"

        try:
            df = pd.read_csv(filepath)
            print(f"[OK] Loaded {len(df)} radar observations")
            return df
        except FileNotFoundError:
            print(f"[ERROR] File not found: {filepath}")
            return None

    @staticmethod
    def get_radar_summary(df: pd.DataFrame) -> Dict:
        """Get summary statistics of radar data."""
        if df is None:
            return {}

        summary = {
            "total_observations": len(df),
            "time_range": f"{df['timestamp'].min()} to {df['timestamp'].max()}",
            "unique_tracks": df['track_id'].nunique(),
            "object_classes": df['object_class'].unique().tolist(),
            "class_distribution": df['object_class'].value_counts().to_dict(),
            "range_stats": {
                "min": df['range_m'].min(),
                "max": df['range_m'].max(),
                "mean": df['range_m'].mean(),
            },
            "confidence_stats": {
                "min": df['confidence'].min(),
                "max": df['confidence'].max(),
                "mean": df['confidence'].mean(),
            },
        }
        return summary

    @staticmethod
    def get_high_confidence_targets(df: pd.DataFrame, threshold: float = 0.8) -> pd.DataFrame:
        """Filter targets by confidence threshold."""
        return df[df['confidence'] >= threshold]

    @staticmethod
    def get_targets_by_class(df: pd.DataFrame, object_class: str) -> pd.DataFrame:
        """Get all observations for a specific object class."""
        return df[df['object_class'] == object_class]

    @staticmethod
    def get_track_by_id(df: pd.DataFrame, track_id: int) -> pd.DataFrame:
        """Get all observations for a specific track ID."""
        return df[df['track_id'] == track_id]

    @staticmethod
    def get_observations_by_time_range(df: pd.DataFrame, start_time: str, end_time: str) -> pd.DataFrame:
        """Get observations within time range."""
        df_copy = df.copy()
        df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
        return df_copy[(df_copy['timestamp'] >= start_time) & (df_copy['timestamp'] <= end_time)]


def display_radar_dashboard():
    """Display radar data summary dashboard."""
    loader = RadarDatasetLoader()
    df = loader.load_radar_data()

    if df is None:
        return

    summary = loader.get_radar_summary(df)

    print("\n" + "="*70)
    print("RADAR OBSERVATION DASHBOARD")
    print("="*70 + "\n")

    print(f"Total Observations: {summary['total_observations']:,}")
    print(f"Time Range: {summary['time_range']}")
    print(f"Unique Tracks: {summary['unique_tracks']}")
    print(f"\nObject Classes:")
    for obj_class, count in summary['class_distribution'].items():
        pct = (count / summary['total_observations']) * 100
        print(f"  - {obj_class:12} {count:6,} observations ({pct:5.1f}%)")

    print(f"\nRange Statistics (meters):")
    print(f"  Min:  {summary['range_stats']['min']:8.1f}")
    print(f"  Max:  {summary['range_stats']['max']:8.1f}")
    print(f"  Mean: {summary['range_stats']['mean']:8.1f}")

    print(f"\nConfidence Statistics (0-1):")
    print(f"  Min:  {summary['confidence_stats']['min']:8.2f}")
    print(f"  Max:  {summary['confidence_stats']['max']:8.2f}")
    print(f"  Mean: {summary['confidence_stats']['mean']:8.2f}")

    print(f"\nHigh Confidence Targets (>0.8):")
    high_conf = loader.get_high_confidence_targets(df)
    print(f"  Count: {len(high_conf):,} ({(len(high_conf)/len(df)*100):.1f}%)")

    print(f"\nSample Observations (first 5):")
    print(df.head().to_string())

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    display_radar_dashboard()

    # Example usage
    loader = RadarDatasetLoader()
    df = loader.load_radar_data()

    if df is not None:
        print("\nExample: Get all person detections")
        persons = loader.get_targets_by_class(df, "person")
        print(f"  Found {len(persons)} person detections\n")

        print("Example: Get track 1002")
        track = loader.get_track_by_id(df, 1002)
        print(f"  Track 1002 has {len(track)} observations\n")

        print("Example: Get high-confidence targets")
        high_conf = loader.get_high_confidence_targets(df, threshold=0.85)
        print(f"  Found {len(high_conf)} observations with confidence > 0.85")
