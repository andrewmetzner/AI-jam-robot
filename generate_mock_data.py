#!/usr/bin/env python3
"""
Generate mock datasets for all uncovered rover sensors.
Matches the style and time-range of existing CSV files.
Run once: python generate_mock_data.py
"""

import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

DATASETS_DIR = Path(__file__).parent / "datasets"
DATASETS_DIR.mkdir(exist_ok=True)

START = datetime(2026, 6, 29, 12, 0, 0)
DURATION_S = 3600      # 1 hour
INTERVAL_S = 2         # one row every 2 s  →  1800 rows per file

rng = random.Random(42)  # deterministic


def ts(offset_s):
    return (START + timedelta(seconds=offset_s)).strftime("%Y-%m-%dT%H:%M:%S")


def noise(base, pct=0.05):
    return base * (1 + rng.uniform(-pct, pct))


def write(filename, fieldnames, rows):
    path = DATASETS_DIR / filename
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {len(rows):,} rows -> {path.name}")


# ─────────────────────────────────────────────────────────────
# 1. Environmental probe pack (temp, humidity, pressure, air-quality, radiation, EC)
#    One combined row per timestamp from the onboard instrument pack.
# ─────────────────────────────────────────────────────────────
def gen_env_probe():
    fields = [
        "timestamp",
        "temp_c",
        "humidity_pct",
        "pressure_hpa",
        "abs_470nm",     # light absorbance at 470 nm (blue)
        "abs_850nm",     # light absorbance at 850 nm (NIR)
        "scattering_m1", # scattering coefficient m⁻¹
        "pm25_ug_m3",    # particulate matter 2.5 µm
        "cosmic_rad_usv_h",
        "ec_ms_cm",
        "sensor_voltage_v",
        "gps_lat",
        "gps_lon",
    ]
    rows = []
    lat0, lon0 = 40.8672, -72.8827   # BNL-ish coords
    for s in range(0, DURATION_S, INTERVAL_S):
        t = s / DURATION_S   # 0 → 1
        # slow sinusoidal drift to simulate a real traverse
        lat = lat0 + 0.001 * math.sin(2 * math.pi * t)
        lon = lon0 + 0.001 * t
        rows.append({
            "timestamp":         ts(s),
            "temp_c":            round(noise(22.5 + 4 * math.sin(math.pi * t)), 3),
            "humidity_pct":      round(noise(45.0 - 8 * t), 2),
            "pressure_hpa":      round(noise(1013.25 - 1.5 * t), 2),
            "abs_470nm":         round(noise(0.12 + 0.04 * t), 4),
            "abs_850nm":         round(noise(0.08 + 0.02 * t), 4),
            "scattering_m1":     round(noise(0.055 + 0.015 * math.sin(4 * math.pi * t)), 4),
            "pm25_ug_m3":        round(noise(8.2 + 3.0 * rng.random()), 2),
            "cosmic_rad_usv_h":  round(noise(0.058 + 0.012 * t), 4),
            "ec_ms_cm":          round(noise(0.88 + 0.40 * t), 4),
            "sensor_voltage_v":  round(noise(3.31), 3),
            "gps_lat":           round(lat, 7),
            "gps_lon":           round(lon, 7),
        })
    write("mock_env_probe_1hour.csv", fields, rows)


# ─────────────────────────────────────────────────────────────
# 2. XRD – X-Ray Diffraction  (one scan per ~60 s at sample sites)
# ─────────────────────────────────────────────────────────────
def gen_xrd():
    mineral_pool = [
        ("plagioclase",    45, 58, "feldspar group"),
        ("pyroxene",       34, 48, "chain silicate"),
        ("olivine",        22, 36, "orthosilicate"),
        ("ilmenite",       12, 20, "oxide mineral"),
        ("anorthosite",    40, 54, "calcium feldspar"),
        ("troilite",        8, 15, "iron sulfide"),
        ("spinel",         10, 18, "oxide"),
        ("apatite",         5, 10, "phosphate"),
        ("glass_basaltic", 15, 28, "amorphous phase"),
    ]
    fields = [
        "timestamp", "sample_id", "site_x_m", "site_y_m",
        "primary_mineral", "primary_pct",
        "secondary_mineral", "secondary_pct",
        "tertiary_mineral", "tertiary_pct",
        "amorphous_pct", "crystallinity_index",
        "peak_2theta_deg", "d_spacing_angstrom",
        "scan_duration_s", "detector_counts", "confidence",
    ]
    rows = []
    for i, s in enumerate(range(0, DURATION_S, 60)):
        m1, lo1, hi1, _ = rng.choice(mineral_pool)
        m2, lo2, hi2, _ = rng.choice([m for m in mineral_pool if m[0] != m1])
        m3, lo3, hi3, _ = rng.choice([m for m in mineral_pool if m[0] not in (m1, m2)])
        p1 = rng.randint(lo1, hi1)
        p2_max = min(hi2, 100 - p1 - 5)
        p2 = rng.randint(lo2, p2_max) if lo2 <= p2_max else lo2
        p3_max = min(hi3, 100 - p1 - p2 - 3)
        p3 = max(0, rng.randint(2, p3_max) if 2 <= p3_max else 2)
        amorphous = max(0, 100 - p1 - p2 - p3)
        rows.append({
            "timestamp":          ts(s),
            "sample_id":          f"XRD-{i+1:04d}",
            "site_x_m":           round(rng.uniform(-60, 60), 2),
            "site_y_m":           round(rng.uniform(-60, 60), 2),
            "primary_mineral":    m1,
            "primary_pct":        p1,
            "secondary_mineral":  m2,
            "secondary_pct":      p2,
            "tertiary_mineral":   m3,
            "tertiary_pct":       p3,
            "amorphous_pct":      amorphous,
            "crystallinity_index":round(rng.uniform(0.55, 0.95), 3),
            "peak_2theta_deg":    round(rng.uniform(25.0, 45.0), 2),
            "d_spacing_angstrom": round(rng.uniform(2.0, 4.5), 3),
            "scan_duration_s":    rng.randint(30, 90),
            "detector_counts":    rng.randint(8000, 32000),
            "confidence":         round(rng.uniform(0.72, 0.99), 2),
        })
    write("mock_xrd_observations_1hour.csv", fields, rows)


# ─────────────────────────────────────────────────────────────
# 3. XRF – X-Ray Fluorescence  (elemental composition, ~45 s cadence)
# ─────────────────────────────────────────────────────────────
def gen_xrf():
    fields = [
        "timestamp", "sample_id", "site_x_m", "site_y_m",
        "Si_wt_pct", "Al_wt_pct", "Fe_wt_pct", "Ca_wt_pct",
        "Mg_wt_pct", "Na_wt_pct", "K_wt_pct",  "Ti_wt_pct",
        "Mn_wt_pct", "P_wt_pct",
        "Cr_ppm", "Ni_ppm", "Sr_ppm", "Zr_ppm",
        "loi_wt_pct",   # loss on ignition
        "scan_kv", "scan_ua", "integration_time_s", "confidence",
    ]
    rows = []
    for i, s in enumerate(range(0, DURATION_S, 45)):
        # Lunar-like basalt composition with per-site noise
        base = {"Si":45.5,"Al":12.8,"Fe":8.4,"Ca":9.7,"Mg":7.2,"Na":1.4,"K":0.35,"Ti":1.9,"Mn":0.18,"P":0.12}
        el = {k: round(max(0, noise(v, 0.15)), 3) for k, v in base.items()}
        total = sum(el.values())
        loi = round(max(0, 100 - total - rng.uniform(0, 1.5)), 2)
        rows.append({
            "timestamp":       ts(s),
            "sample_id":       f"XRF-{i+1:04d}",
            "site_x_m":        round(rng.uniform(-60, 60), 2),
            "site_y_m":        round(rng.uniform(-60, 60), 2),
            "Si_wt_pct":       el["Si"], "Al_wt_pct": el["Al"],
            "Fe_wt_pct":       el["Fe"], "Ca_wt_pct": el["Ca"],
            "Mg_wt_pct":       el["Mg"], "Na_wt_pct": el["Na"],
            "K_wt_pct":        el["K"],  "Ti_wt_pct": el["Ti"],
            "Mn_wt_pct":       el["Mn"], "P_wt_pct":  el["P"],
            "Cr_ppm":          round(noise(420, 0.2)),
            "Ni_ppm":          round(noise(95, 0.2)),
            "Sr_ppm":          round(noise(130, 0.2)),
            "Zr_ppm":          round(noise(60, 0.2)),
            "loi_wt_pct":      loi,
            "scan_kv":         40,
            "scan_ua":         20,
            "integration_time_s": rng.randint(20, 60),
            "confidence":      round(rng.uniform(0.80, 0.99), 2),
        })
    write("mock_xrf_observations_1hour.csv", fields, rows)


# ─────────────────────────────────────────────────────────────
# 4. GPR – Ground Penetrating Radar  (a profile every ~30 s)
# ─────────────────────────────────────────────────────────────
def gen_gpr():
    feature_pool = [
        "void",        # lava tube / cavity
        "ice_lens",    # sub-surface ice
        "rock_layer",  # lithological boundary
        "fracture",    # crack system
        "regolith",    # loose material
        "none",
    ]
    fields = [
        "timestamp", "profile_id",
        "start_x_m", "start_y_m", "end_x_m", "end_y_m",
        "frequency_mhz",
        "max_depth_m", "resolution_cm",
        "feature_detected", "feature_depth_m", "feature_thickness_m",
        "reflector_amplitude_db", "two_way_travel_ns",
        "dielectric_constant", "estimated_velocity_m_ns",
        "confidence", "notes",
    ]
    notes_pool = ["clear signal","minor clutter","high attenuation","excellent penetration","multipath present"]
    rows = []
    for i, s in enumerate(range(0, DURATION_S, 30)):
        feat = rng.choice(feature_pool)
        has_feat = feat != "none"
        rows.append({
            "timestamp":             ts(s),
            "profile_id":            f"GPR-{i+1:04d}",
            "start_x_m":            round(rng.uniform(-50, 50), 1),
            "start_y_m":            round(rng.uniform(-50, 50), 1),
            "end_x_m":              round(rng.uniform(-50, 50), 1),
            "end_y_m":              round(rng.uniform(-50, 50), 1),
            "frequency_mhz":        rng.choice([200, 400, 900]),
            "max_depth_m":          round(rng.uniform(3.0, 12.0), 1),
            "resolution_cm":        rng.choice([5, 10, 20]),
            "feature_detected":     feat,
            "feature_depth_m":      round(rng.uniform(0.5, 8.0), 2) if has_feat else "",
            "feature_thickness_m":  round(rng.uniform(0.1, 2.5), 2) if has_feat else "",
            "reflector_amplitude_db": round(noise(-18, 0.3), 1),
            "two_way_travel_ns":    round(rng.uniform(5.0, 80.0), 1),
            "dielectric_constant":  round(rng.uniform(3.0, 8.5), 2),
            "estimated_velocity_m_ns": round(rng.uniform(0.10, 0.17), 3),
            "confidence":           round(rng.uniform(0.65, 0.97), 2),
            "notes":                rng.choice(notes_pool),
        })
    write("mock_gpr_observations_1hour.csv", fields, rows)


# ─────────────────────────────────────────────────────────────
# 5. pH Probe  (one reading per ~15 s at sampling sites)
# ─────────────────────────────────────────────────────────────
def gen_ph():
    fields = [
        "timestamp", "sample_id", "site_x_m", "site_y_m",
        "ph_value", "ph_temp_corrected",
        "oxidation_reduction_potential_mv",
        "ionic_strength_mol_l",
        "buffer_capacity",
        "sample_depth_cm",
        "moisture_pct",
        "electrode_mv", "electrode_temp_c", "confidence",
    ]
    rows = []
    for i, s in enumerate(range(0, DURATION_S, 15)):
        ph = round(noise(7.8 + 0.6 * math.sin(2 * math.pi * i / 240), 0.04), 2)
        rows.append({
            "timestamp":                     ts(s),
            "sample_id":                     f"PH-{i+1:04d}",
            "site_x_m":                      round(rng.uniform(-60, 60), 2),
            "site_y_m":                      round(rng.uniform(-60, 60), 2),
            "ph_value":                      ph,
            "ph_temp_corrected":             round(ph + rng.uniform(-0.05, 0.05), 2),
            "oxidation_reduction_potential_mv": round(noise(+180, 0.15), 1),
            "ionic_strength_mol_l":          round(noise(0.012, 0.12), 4),
            "buffer_capacity":               round(noise(0.048, 0.10), 4),
            "sample_depth_cm":               rng.choice([2, 5, 10, 15]),
            "moisture_pct":                  round(noise(14.5, 0.10), 2),
            "electrode_mv":                  round(noise(-45, 0.08), 2),
            "electrode_temp_c":              round(noise(22.5, 0.03), 2),
            "confidence":                    round(rng.uniform(0.88, 0.99), 2),
        })
    write("mock_ph_observations_1hour.csv", fields, rows)


# ─────────────────────────────────────────────────────────────
# 6. Soil Core Sampler  (0–15 cm, one core per ~120 s)
# ─────────────────────────────────────────────────────────────
def gen_soil_core():
    texture_pool = ["sandy loam","loam","silty loam","clay loam","silt","regolith breccia"]
    color_pool   = ["dark grey","medium grey","light grey","brownish grey","reddish grey"]
    fields = [
        "timestamp", "core_id", "site_x_m", "site_y_m",
        "depth_top_cm", "depth_bot_cm",
        "bulk_density_g_cm3",
        "porosity_pct",
        "moisture_content_pct",
        "organic_carbon_pct",
        "total_nitrogen_pct",
        "texture_class",
        "color_munsell",
        "rock_fragment_pct",
        "compaction_n_cm2",
        "sample_mass_g",
        "retrieved_pct",   # % of target core actually recovered
        "confidence",
    ]
    rows = []
    for i, s in enumerate(range(0, DURATION_S, 120)):
        top = rng.choice([0, 5, 10])
        bot = top + rng.choice([5, 10, 15])
        rows.append({
            "timestamp":           ts(s),
            "core_id":             f"CORE-{i+1:04d}",
            "site_x_m":           round(rng.uniform(-60, 60), 2),
            "site_y_m":           round(rng.uniform(-60, 60), 2),
            "depth_top_cm":       top,
            "depth_bot_cm":       min(bot, 15),
            "bulk_density_g_cm3": round(noise(1.55, 0.08), 3),
            "porosity_pct":       round(noise(41.5, 0.08), 2),
            "moisture_content_pct": round(noise(12.8, 0.12), 2),
            "organic_carbon_pct": round(noise(0.31, 0.20), 3),
            "total_nitrogen_pct": round(noise(0.028, 0.15), 4),
            "texture_class":      rng.choice(texture_pool),
            "color_munsell":      rng.choice(color_pool),
            "rock_fragment_pct":  round(rng.uniform(5, 40), 1),
            "compaction_n_cm2":   round(noise(18.5, 0.15), 2),
            "sample_mass_g":      round(noise(24.5, 0.10), 2),
            "retrieved_pct":      round(rng.uniform(70, 100), 1),
            "confidence":         round(rng.uniform(0.82, 0.99), 2),
        })
    write("mock_soil_core_1hour.csv", fields, rows)


# ─────────────────────────────────────────────────────────────
# 7. Gas Syringe Sampler  (atmospheric + soil gas, one per ~90 s)
# ─────────────────────────────────────────────────────────────
def gen_gas_syringe():
    fields = [
        "timestamp", "sample_id", "site_x_m", "site_y_m",
        "sample_source",     # atmosphere | soil_5cm | soil_15cm
        "N2_pct", "O2_pct", "Ar_pct", "CO2_ppm", "CH4_ppb",
        "H2_ppb", "H2S_ppb", "SO2_ppb", "N2O_ppb",
        "total_voc_ppb",
        "sample_pressure_hpa",
        "sample_temp_c",
        "syringe_volume_ml",
        "collection_time_s",
        "confidence",
    ]
    sources = ["atmosphere", "soil_5cm", "soil_15cm"]
    rows = []
    for i, s in enumerate(range(0, DURATION_S, 90)):
        src = rng.choice(sources)
        is_soil = src.startswith("soil")
        rows.append({
            "timestamp":           ts(s),
            "sample_id":           f"GAS-{i+1:04d}",
            "site_x_m":           round(rng.uniform(-60, 60), 2),
            "site_y_m":           round(rng.uniform(-60, 60), 2),
            "sample_source":       src,
            # Soil gas has elevated CO2, CH4
            "N2_pct":             round(noise(78.08 if not is_soil else 70.0, 0.005), 3),
            "O2_pct":             round(noise(20.95 if not is_soil else 18.5, 0.01), 3),
            "Ar_pct":             round(noise(0.93, 0.01), 3),
            "CO2_ppm":            round(noise(415 if not is_soil else 2800, 0.08)),
            "CH4_ppb":            round(noise(1900 if not is_soil else 8500, 0.15)),
            "H2_ppb":             round(noise(550, 0.20)),
            "H2S_ppb":            round(max(0, noise(0.8 if not is_soil else 12.0, 0.30)), 2),
            "SO2_ppb":            round(max(0, noise(0.2, 0.40)), 2),
            "N2O_ppb":            round(noise(330, 0.04)),
            "total_voc_ppb":      round(noise(25 if not is_soil else 180, 0.20)),
            "sample_pressure_hpa": round(noise(1013.0, 0.01), 2),
            "sample_temp_c":      round(noise(22.5, 0.04), 2),
            "syringe_volume_ml":  rng.choice([20, 50, 100]),
            "collection_time_s":  rng.randint(10, 60),
            "confidence":         round(rng.uniform(0.82, 0.99), 2),
        })
    write("mock_gas_syringe_1hour.csv", fields, rows)


if __name__ == "__main__":
    print("Generating mock sensor datasets...\n")
    gen_env_probe()
    gen_xrd()
    gen_xrf()
    gen_gpr()
    gen_ph()
    gen_soil_core()
    gen_gas_syringe()
    print("\nDone! All files written to datasets/")
