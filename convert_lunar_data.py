"""
Convert the real Lunar datasets into the env-probe CSV format the dashboard
already consumes (same columns as the old mock_env_probe_1hour.csv).

Sources:
  - Mock_Lunar_Environment_Dataset_2026-06-29_1200.xlsx  (60 rows, 1/min)
        Ambient Temp, Regolith Temps, Solar Illumination, Humidity, Pressure, Radiation
  - mock_lunar_cosmic_radiation_observations_1hour.xlsx   (3600 rows, 1/s)
        dose_rate_usv_h, voltage_v, sensor_temp_c, solar_particle_event
  - mock_lunar_lidar_observations_1hour.csv               (regolith_dust_backscatter -> PM proxy)

Output: datasets/lunar_env_probe_1hour.csv with columns:
  timestamp, temp_c, humidity_pct, pressure_hpa, abs_470nm, abs_850nm,
  scattering_m1, pm25_ug_m3, cosmic_rad_usv_h, ec_ms_cm, sensor_voltage_v,
  gps_lat, gps_lon
"""

import random
from pathlib import Path
import pandas as pd

DATA = Path(__file__).parent / "datasets"
rng = random.Random(42)

# South Pole-Aitken Basin selenographic centre (approx): 53°S, 169°W
SELENO_LAT = -53.0
SELENO_LON = -169.0


def load_env():
    df = pd.read_excel(DATA / "Mock_Lunar_Environment_Dataset_2026-06-29_1200.xlsx",
                       sheet_name="Lunar_Environment")
    # Normalise the mojibake column names (°/µ got mangled in the xlsx)
    df.columns = [c.strip() for c in df.columns]
    rename = {}
    for c in df.columns:
        cl = c.lower()
        if cl.startswith("timestamp"):            rename[c] = "timestamp"
        elif cl.startswith("ambient temp"):       rename[c] = "ambient_temp_c"
        elif "regolith temp 5cm" in cl:           rename[c] = "regolith_5cm_c"
        elif "solar illumination" in cl:          rename[c] = "solar_pct"
        elif cl.startswith("humidity"):           rename[c] = "humidity_pct"
        elif cl.startswith("pressure"):           rename[c] = "pressure_pa"
        elif cl.startswith("radiation"):          rename[c] = "radiation_usv_h"
    return df.rename(columns=rename)


def load_cosmic():
    df = pd.read_excel(DATA / "mock_lunar_cosmic_radiation_observations_1hour.xlsx",
                       sheet_name="in")
    return df


def load_dust_proxy(n):
    df = pd.read_csv(DATA / "mock_lunar_lidar_observations_1hour.csv",
                     usecols=["mission_elapsed_s", "regolith_dust_backscatter"])
    # average dust backscatter per elapsed second
    per_s = df.groupby("mission_elapsed_s")["regolith_dust_backscatter"].mean()
    return per_s


def main():
    env = load_env()              # 60 rows @ 1/min
    cosmic = load_cosmic()        # 3600 rows @ 1/s
    dust = load_dust_proxy(3600)

    rows = []
    # Build one row every 2 s for an hour -> 1800 rows (matches old cadence)
    for i in range(1800):
        elapsed_s = i * 2
        minute = min(elapsed_s // 60, len(env) - 1)
        e = env.iloc[minute]

        # Cosmic radiation: per-second detail, take the matching second
        c = cosmic.iloc[min(elapsed_s, len(cosmic) - 1)]

        # Real lunar values
        temp_c   = float(e["ambient_temp_c"])
        humidity = float(e["humidity_pct"])          # ~0 (no atmosphere)
        pres_pa  = float(e["pressure_pa"])           # ~0 Pa (vacuum)
        pres_hpa = pres_pa / 100.0                   # convert Pa -> hPa
        rad      = float(c["dose_rate_usv_h"])       # detailed cosmic dose
        voltage  = float(c["voltage_v"])
        spe      = str(c["solar_particle_event"]).lower() == "yes"

        # Dust (PM2.5 proxy from regolith backscatter, scaled to µg/m³)
        d_back = float(dust.get(elapsed_s, dust.iloc[min(elapsed_s, len(dust)-1)]))
        pm25 = round(d_back * 12.0 + rng.uniform(0, 0.5), 2)

        # Vacuum -> air-quality optics are essentially zero with sensor noise
        abs470 = round(rng.uniform(0.0, 0.004), 4)
        abs850 = round(rng.uniform(0.0, 0.003), 4)
        scatter = round(d_back * 0.02 + rng.uniform(0, 0.002), 4)

        # Dry regolith electrical conductivity is extremely low (near-insulator)
        ec = round(rng.uniform(0.001, 0.02), 4)

        # Selenographic position with small rover drift
        lat = round(SELENO_LAT + rng.uniform(-0.02, 0.02), 6)
        lon = round(SELENO_LON + rng.uniform(-0.02, 0.02), 6)

        ts = pd.Timestamp("2026-06-29T12:00:00") + pd.Timedelta(seconds=elapsed_s)

        rows.append({
            "timestamp":        ts.isoformat(),
            "temp_c":           round(temp_c, 3),
            "humidity_pct":     round(humidity, 2),
            "pressure_hpa":     round(pres_hpa, 4),
            "abs_470nm":        abs470,
            "abs_850nm":        abs850,
            "scattering_m1":    scatter,
            "pm25_ug_m3":       pm25,
            "cosmic_rad_usv_h": round(rad, 3),
            "ec_ms_cm":         ec,
            "sensor_voltage_v": round(voltage, 3),
            "gps_lat":          lat,
            "gps_lon":          lon,
        })

    out = DATA / "lunar_env_probe_1hour.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Wrote {len(rows)} rows -> {out}")
    print("Sample row:")
    print(pd.DataFrame(rows).iloc[0].to_string())
    print("\nRanges:")
    df = pd.DataFrame(rows)
    for col in ["temp_c", "humidity_pct", "pressure_hpa", "cosmic_rad_usv_h", "pm25_ug_m3"]:
        print(f"  {col}: {df[col].min()} .. {df[col].max()}")


if __name__ == "__main__":
    main()
