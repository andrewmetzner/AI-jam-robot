"""Generate a modeled lunar probability surface from mission datasets."""

from datetime import datetime
from pathlib import Path
import math
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from data.sensor_loader import SensorDataLoader


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, float(value)))


# ── Resource Utilization dataset (real lat/lon resource survey) ────────────────
_RESOURCE_CSV = Path(__file__).parent.parent / "datasets" / "resource_utilization.csv"
_resource_df: Optional[pd.DataFrame] = None


def _load_resource_df() -> Optional[pd.DataFrame]:
    global _resource_df
    if _resource_df is None:
        try:
            _resource_df = pd.read_csv(_RESOURCE_CSV)
        except Exception:
            _resource_df = pd.DataFrame()
    return _resource_df if not _resource_df.empty else None


def _resource_grid(rows: int, cols: int) -> Dict:
    """
    Bin the spatial resource survey into the probability grid by lat/lon, returning
    normalized per-cell resource/ice/radiation/agriculture/toxicity layers.
    """
    df = _load_resource_df()
    if df is None:
        return {}

    # Longitude -180..180 -> col 0..cols-1 ; Latitude 90..-90 -> row 0..rows-1
    col_idx = ((df["Longitude"] + 180.0) / 360.0 * cols).clip(0, cols - 1).astype(int)
    row_idx = ((90.0 - df["Latitude"]) / 180.0 * rows).clip(0, rows - 1).astype(int)
    df = df.assign(_row=row_idx, _col=col_idx)

    layers = {}
    grouped = df.groupby(["_row", "_col"])
    for (r, c), g in grouped:
        layers[(int(r), int(c))] = {
            "resource": _clamp(g["Resource_Score"].mean() / 100.0),
            "ice": _clamp(g["Ice_Probability_%"].mean() / 100.0),
            "radiation": _clamp(g["Cosmic_Radiation_mSv_day"].mean() / 3.5),
            "toxicity": _clamp(g["Toxicity_Index"].mean() / 100.0),
            "agriculture": _clamp(g["Agriculture_Score"].mean() / 100.0),
            "extractable": float((g["Resource_Extractable"] == "Yes").mean()),
            "samples": int(len(g)),
        }
    return layers


class LunarProbabilityMapGenerator:
    """Build a probability map for lunar traversal and sampling."""

    def __init__(self, rows: int = 10, cols: int = 16):
        self.rows = rows
        self.cols = cols

    @staticmethod
    def _score_resource_potential(soil_summary: Dict) -> float:
        volatile_ratio = _clamp(soil_summary.get("volatile_ratio", 0.0))
        quality_ratio = _clamp(soil_summary.get("good_quality_ratio", 0.0))
        bulk_density = _clamp(1.0 - soil_summary.get("avg_bulk_density", 0.0) / 2.9)
        moisture = _clamp(soil_summary.get("avg_moisture", 0.0) / 12.0)
        cohesion = _clamp(1.0 - soil_summary.get("avg_cohesion", 0.0) / 2.0)
        fragments = _clamp(1.0 - soil_summary.get("avg_rock_fragment_pct", 0.0) / 20.0)

        return _clamp(
            0.28 * volatile_ratio +
            0.20 * quality_ratio +
            0.17 * bulk_density +
            0.15 * moisture +
            0.10 * cohesion +
            0.10 * fragments
        )

    def generate_map(self, rows: int = None, cols: int = None) -> Dict:
        """Generate a grid of modeled lunar probabilities."""
        env = SensorDataLoader.load_env_probe_data()
        soil = SensorDataLoader.load_soil_core_data()

        if not env or not soil:
            return {
                "error": "Required datasets are unavailable",
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }

        rows = rows or self.rows
        cols = cols or self.cols

        env_summary = env["summary"]
        soil_summary = soil["summary"]

        seed = int(
            env_summary.get("radiation_mean", 0.0) * 1000
            + env_summary.get("pm25_mean", 0.0) * 100
            + soil_summary.get("avg_bulk_density", 0.0) * 1000
        ) & 0xFFFFFFFF
        rng = np.random.default_rng(seed)

        base_radiation = _clamp(env_summary.get("radiation_mean", 0.0) / 160.0)
        base_heat = _clamp(abs(env_summary.get("temp_range", {}).get("mean", 0.0) + 50.0) / 170.0)
        base_dust = _clamp(env_summary.get("pm25_mean", 0.0) / 12.0)
        base_resource = self._score_resource_potential(soil_summary)

        # Real spatial resource survey, binned into the grid (may be empty)
        resource_layers = _resource_grid(rows, cols)

        cells: List[Dict] = []

        for row in range(rows):
            for col in range(cols):
                x_norm = (col / max(cols - 1, 1)) * 2.0 - 1.0
                y_norm = (row / max(rows - 1, 1)) * 2.0 - 1.0
                radius = math.sqrt(x_norm * x_norm + y_norm * y_norm)

                basin = _clamp(1.0 - radius)
                rim = _clamp(1.0 - abs(radius - 0.65) / 0.45)
                ridge = _clamp((math.sin((x_norm + y_norm) * math.pi * 1.3) + math.cos((x_norm - y_norm) * math.pi * 0.9) + 2.0) / 4.0)
                east_west = _clamp((x_norm + 1.0) / 2.0)
                north_south = _clamp((1.0 - y_norm) / 2.0)

                local_radiation = _clamp(base_radiation + 0.30 * east_west + 0.10 * ridge + rng.normal(0, 0.02))
                local_heat = _clamp(base_heat + 0.18 * (1.0 - basin) + 0.08 * ridge + rng.normal(0, 0.02))
                local_dust = _clamp(base_dust + 0.12 * basin + 0.08 * rim + rng.normal(0, 0.02))
                terrain_risk = _clamp(0.15 * east_west + 0.10 * north_south + 0.12 * ridge)

                # Real resource-survey layer for this cell (if available)
                rlayer = resource_layers.get((row, col))
                r_resource = rlayer["resource"] if rlayer else None
                r_ice = rlayer["ice"] if rlayer else 0.0
                r_tox = rlayer["toxicity"] if rlayer else 0.0
                r_agri = rlayer["agriculture"] if rlayer else 0.0
                r_rad = rlayer["radiation"] if rlayer else None

                # Blend survey radiation into the modeled radiation field
                if r_rad is not None:
                    local_radiation = _clamp(0.6 * local_radiation + 0.4 * r_rad)

                hazard_probability = _clamp(
                    0.40 * local_radiation +
                    0.18 * local_heat +
                    0.16 * local_dust +
                    0.12 * terrain_risk +
                    0.14 * r_tox            # surveyed toxicity raises hazard
                )
                modeled_resource = _clamp(
                    base_resource +
                    0.25 * rim +
                    0.12 * (1.0 - hazard_probability) +
                    0.08 * basin -
                    0.10 * local_radiation
                )
                # Prefer the real surveyed resource score where we have coverage
                if r_resource is not None:
                    resource_probability = _clamp(0.45 * modeled_resource + 0.55 * r_resource + 0.10 * r_ice)
                else:
                    resource_probability = modeled_resource
                drillability_probability = _clamp(
                    0.45 * (1.0 - soil_summary.get("avg_bulk_density", 0.0) / 2.9) +
                    0.30 * (1.0 - soil_summary.get("avg_cohesion", 0.0) / 2.0) +
                    0.15 * (1.0 - local_heat) +
                    0.10 * (1.0 - local_dust)
                )
                safe_probability = _clamp(1.0 - hazard_probability + 0.10 * (1.0 - resource_probability))
                composite_probability = _clamp(
                    0.40 * safe_probability +
                    0.35 * resource_probability +
                    0.25 * drillability_probability
                )

                if r_ice >= 0.70:
                    label = "Ice Deposit"
                elif r_agri >= 0.65 and hazard_probability < 0.6:
                    label = "Agri-Viable Soil"
                elif composite_probability >= 0.70:
                    label = "Prime Survey Zone"
                elif resource_probability >= 0.70 and drillability_probability >= 0.60:
                    label = "Prime Sample Zone"
                elif safe_probability >= 0.72:
                    label = "Transit Corridor"
                elif hazard_probability >= 0.75:
                    label = "Radiation Watch"
                else:
                    label = "Survey Zone"

                cells.append({
                    "row": row,
                    "col": col,
                    "x_norm": round(x_norm, 3),
                    "y_norm": round(y_norm, 3),
                    "safe_probability": round(safe_probability, 3),
                    "resource_probability": round(resource_probability, 3),
                    "hazard_probability": round(hazard_probability, 3),
                    "drillability_probability": round(drillability_probability, 3),
                    "composite_probability": round(composite_probability, 3),
                    "radiation_probability": round(local_radiation, 3),
                    "dust_probability": round(local_dust, 3),
                    "terrain_risk": round(terrain_risk, 3),
                    "ice_probability": round(r_ice, 3),
                    "agriculture_score": round(r_agri, 3),
                    "toxicity": round(r_tox, 3),
                    "surveyed": rlayer is not None,
                    "label": label,
                })

        best_cell = max(cells, key=lambda cell: cell["composite_probability"])
        safest_cell = max(cells, key=lambda cell: cell["safe_probability"])
        richest_cell = max(cells, key=lambda cell: cell["resource_probability"])
        riskiest_cell = max(cells, key=lambda cell: cell["hazard_probability"])
        iciest_cell = max(cells, key=lambda cell: cell["ice_probability"])
        agri_cell = max(cells, key=lambda cell: cell["agriculture_score"])

        resource_df = _load_resource_df()
        resource_rows = 0 if resource_df is None else int(len(resource_df))
        surveyed_cells = sum(1 for c in cells if c["surveyed"])

        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "map_type": "modeled_lunar_probability_surface",
            "source": {
                "environment_rows": env_summary.get("total_observations", 0),
                "soil_samples": soil_summary.get("total_samples", 0),
                "resource_survey_points": resource_rows,
                "surveyed_cells": surveyed_cells,
                "note": "Probability surface calibrated from the lunar environment + soil datasets, "
                        "spatially anchored by the FINAL resource-utilization survey (lat/lon resource, ice, agriculture, toxicity).",
            },
            "summary": {
                "rows": rows,
                "cols": cols,
                "average_safe_probability": round(float(np.mean([cell["safe_probability"] for cell in cells])), 3),
                "average_resource_probability": round(float(np.mean([cell["resource_probability"] for cell in cells])), 3),
                "average_hazard_probability": round(float(np.mean([cell["hazard_probability"] for cell in cells])), 3),
                "average_ice_probability": round(float(np.mean([cell["ice_probability"] for cell in cells])), 3),
                "best_cell": best_cell,
                "safest_cell": safest_cell,
                "richest_cell": richest_cell,
                "riskiest_cell": riskiest_cell,
                "iciest_cell": iciest_cell,
                "agri_cell": agri_cell,
            },
            "cells": cells,
        }
