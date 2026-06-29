#!/usr/bin/env python3
"""
Rover Mission Control Web API
Flask-based REST API for rover simulation with WebSocket support
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import threading
import time
from datetime import datetime
from pathlib import Path
import uuid

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Import existing rover systems
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
import pandas as pd
from data.datasets import DatasetLoader
from data.sensor_loader import SensorDataLoader

# Global state
active_missions = {}
mission_threads = {}

# ── Load env-probe CSV once at startup ───────────────────────────────────────
# Real Lunar environment data (South Pole-Aitken Basin) converted to the
# env-probe schema by convert_lunar_data.py. Falls back to the old mock set.
_ENV_CSV = Path(__file__).parent / "datasets" / "lunar_env_probe_1hour.csv"
if not _ENV_CSV.exists():
    _ENV_CSV = Path(__file__).parent / "datasets" / "mock_env_probe_1hour.csv"
try:
    _env_df = pd.read_csv(_ENV_CSV)
except Exception:
    _env_df = None

_app_start = time.time()


def _current_env_row():
    """Return the env-probe CSV row that corresponds to now (cycles every hour)."""
    if _env_df is None or len(_env_df) == 0:
        return {}
    elapsed = (time.time() - _app_start) % 3600   # cycle every hour
    idx = int(elapsed / 2) % len(_env_df)          # rows are 2 s apart
    row = _env_df.iloc[idx]
    return {
        "temperature":   round(float(row["temp_c"]),            2),
        "humidity":      round(float(row["humidity_pct"]),       2),
        "pressure":      round(float(row["pressure_hpa"]),       1),
        "abs_470nm":     round(float(row["abs_470nm"]),          4),
        "abs_850nm":     round(float(row["abs_850nm"]),          4),
        "scattering":    round(float(row["scattering_m1"]),      4),
        "pm25":          round(float(row["pm25_ug_m3"]),         2),
        "radiation":     round(float(row["cosmic_rad_usv_h"]),   4),
        "conductivity":  round(float(row["ec_ms_cm"]),           3),
        "gps_lat":       round(float(row["gps_lat"]),            6),
        "gps_lon":       round(float(row["gps_lon"]),            6),
        "row_index":     int(idx),
        "timestamp":     str(row["timestamp"]),
    }


def _live_push_loop():
    """Background thread: push env-probe readings to all clients every 2 s."""
    while True:
        time.sleep(2)
        reading = _current_env_row()
        if reading:
            socketio.emit("live_sensor", reading, to="/")

_push_thread = threading.Thread(target=_live_push_loop, daemon=True)
_push_thread.start()


class MissionSimulator:
    """Simulates rover missions and tracks state."""

    def __init__(self, mission_id, dataset_key, mission_type, use_llm=False):
        self.mission_id = mission_id
        self.dataset_key = dataset_key
        self.mission_type = mission_type
        self.use_llm = use_llm
        self.status = "initializing"
        self.start_time = datetime.now()
        self.current_location = 0
        self.samples_found = []
        self.rover_position = [0.0, 0.0]
        self.sensor_readings = {}
        self.battery_level = 100.0
        self.progress = 0
        self.log_entries = []

        # Initialize systems
        self.rover = Rover()
        self.camera = Camera()
        self.depth_sensor = DepthSensor()
        self.thermal_sensor = ThermalSensor()
        self.spectral_analyzer = SpectralAnalyzer()
        self.rock_detector = RockDetector()
        self.rock_classifier = RockClassifier()
        self.sensor_fusion = SensorFusion()
        self.scientist = Scientist(llm_client=None, model="claude-opus")
        self.route_planner = RoutePlanner()

        # Load dataset
        try:
            self.dataset = DatasetLoader.load_dataset(dataset_key)
        except:
            self.dataset = self._create_mock_dataset(dataset_key)

    def _create_mock_dataset(self, dataset_key):
        """Create mock dataset if loader fails."""
        datasets = {
            "simple": {
                "name": "Simple Survey",
                "num_locations": 5,
                "terrain_type": "flat",
                "locations": [
                    {
                        "id": i,
                        "position": [float(i*2), 0.0],
                        "rocks": [
                            {"id": f"rock_{i}_0", "type": "basalt", "confidence": 0.85},
                            {"id": f"rock_{i}_1", "type": "olivine", "confidence": 0.92},
                        ],
                        "hazards": [],
                        "sensors": {
                            "temperature": 15.0 + i,
                            "humidity": 45.0 + i*2,
                            "pressure": 1013.25 - i*0.5,
                            "air_quality": {"absorbance": 0.1 + i*0.02, "scattering": 0.05},
                            "radiation": 0.05 + i*0.01,
                            "conductivity": 0.8 + i*0.05,
                        }
                    }
                    for i in range(5)
                ]
            },
            "complex": {
                "name": "Complex Terrain",
                "num_locations": 8,
                "terrain_type": "hills",
                "locations": [
                    {
                        "id": i,
                        "position": [float(i*2), float(i%2)*3],
                        "rocks": [
                            {"id": f"rock_{i}_0", "type": "anorthosite", "confidence": 0.88},
                            {"id": f"rock_{i}_1", "type": "troctolite", "confidence": 0.80},
                            {"id": f"rock_{i}_2", "type": "norite", "confidence": 0.75},
                        ],
                        "hazards": [{"type": "crater", "depth": 5.0, "distance": 10.0}],
                        "sensors": {
                            "temperature": 10.0 + i,
                            "humidity": 35.0 + i*1.5,
                            "pressure": 1013.0 - i*0.8,
                            "air_quality": {"absorbance": 0.15 + i*0.03, "scattering": 0.08},
                            "radiation": 0.08 + i*0.015,
                            "conductivity": 0.6 + i*0.04,
                        }
                    }
                    for i in range(8)
                ]
            },
            "crater": {
                "name": "Crater Exploration",
                "num_locations": 6,
                "terrain_type": "crater",
                "locations": [
                    {
                        "id": i,
                        "position": [float(i*1.5), float((i-3)**2)*0.5],
                        "rocks": [
                            {"id": f"rock_{i}_0", "type": "basalt", "confidence": 0.90},
                            {"id": f"rock_{i}_1", "type": "olivine", "confidence": 0.87},
                        ],
                        "hazards": [{"type": "subsurface", "depth": 15.0}],
                        "sensors": {
                            "temperature": 5.0 + i*0.5,
                            "humidity": 25.0 + i,
                            "pressure": 1012.0 - i*0.6,
                            "air_quality": {"absorbance": 0.08 + i*0.01, "scattering": 0.04},
                            "radiation": 0.12 + i*0.02,
                            "conductivity": 1.0 + i*0.06,
                        }
                    }
                    for i in range(6)
                ]
            }
        }
        return datasets.get(dataset_key, datasets["simple"])

    def broadcast_update(self, event_type, data):
        """Send update to all connected clients."""
        socketio.emit(event_type, data, to="/")

    def add_log(self, message):
        """Add entry to mission log."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message
        }
        self.log_entries.append(entry)
        self.broadcast_update("log_entry", entry)

    def simulate_location(self, location_idx, location_data):
        """Simulate rover activity at a location."""
        self.current_location = location_idx + 1
        self.rover_position = location_data["position"]

        # Pull readings from the live CSV; no fallback needed since CSV always loads
        csv_row = _current_env_row()
        self.sensor_readings = {
            "temperature":   csv_row.get("temperature",  22.0),
            "humidity":      csv_row.get("humidity",     45.0),
            "pressure":      csv_row.get("pressure",     1013.0),
            "abs_470nm":     csv_row.get("abs_470nm",    0.12),
            "abs_850nm":     csv_row.get("abs_850nm",    0.08),
            "scattering":    csv_row.get("scattering",   0.05),
            "pm25":          csv_row.get("pm25",         8.0),
            "radiation":     csv_row.get("radiation",    0.06),
            "conductivity":  csv_row.get("conductivity", 0.9),
            "gps_lat":       csv_row.get("gps_lat",      0.0),
            "gps_lon":       csv_row.get("gps_lon",      0.0),
            "terrain_slope": location_data.get("terrain_slope", 0.0),
            "depth_average": 5.0 + (location_idx * 0.5),
            "timestamp":     csv_row.get("timestamp",    ""),
        }

        # Hazard detection
        hazards = []
        if self.sensor_readings["radiation"] > 0.10:
            hazards.append({"type": "radiation", "level": "HIGH",
                            "value": self.sensor_readings["radiation"], "unit": "µSv/h"})
        if self.sensor_readings["pm25"] > 15:
            hazards.append({"type": "dust", "level": "HIGH",
                            "value": self.sensor_readings["pm25"], "unit": "µg/m³"})
        slope = self.sensor_readings["terrain_slope"]
        if abs(slope) > 15:
            hazards.append({"type": "slope", "level": "HIGH",
                            "value": slope, "unit": "deg"})
        for h in location_data.get("hazards", []):
            hazards.append({"type": h.get("type", "unknown"), "level": "WARNING",
                            "value": h.get("depth", h.get("distance", 0)), "unit": "m"})
        self.sensor_readings["hazards"] = hazards

        # Log activities
        self.add_log(f"📍 Arrived at Location {location_idx + 1}")
        self.add_log(f"🌡️  Temperature: {self.sensor_readings['temperature']:.1f}°C")
        self.add_log(f"💧 Humidity: {self.sensor_readings['humidity']:.1f}%")
        self.add_log(f"☢️  Radiation: {self.sensor_readings['radiation']:.3f} mSv/h")

        # Simulate rock analysis
        rocks = location_data.get("rocks", [])
        if rocks:
            self.add_log(f"🪨 Detected {len(rocks)} rock samples")
            for rock in rocks:
                sample = {
                    "id": rock["id"],
                    "type": rock["type"],
                    "location": location_idx,
                    "confidence": rock["confidence"],
                    "timestamp": datetime.now().isoformat(),
                    "xrd_mineral": "plagioclase" if "anorthosite" in rock["type"] else "olivine",
                    "xrf_elements": {"Si": 0.45, "Al": 0.12, "Fe": 0.08, "Mg": 0.10},
                    "ph": 8.2 + (location_idx * 0.1),
                    "core_depth": 5.0 + (location_idx * 0.5),
                }
                self.samples_found.append(sample)
                self.add_log(f"  ✓ Sample {rock['id']}: {rock['type'].upper()} ({rock['confidence']:.0%})")

        # Battery drain
        self.battery_level = max(5.0, self.battery_level - 8.0)
        self.add_log(f"🔋 Battery: {self.battery_level:.1f}%")

        # Update progress
        self.progress = min(100, (location_idx + 1) / len(self.dataset["locations"]) * 100)

        # Broadcast update
        self.broadcast_update("mission_update", {
            "mission_id": self.mission_id,
            "status": self.status,
            "progress": self.progress,
            "current_location": self.current_location,
            "rover_position": self.rover_position,
            "battery_level": self.battery_level,
            "samples_count": len(self.samples_found),
            "sensor_readings": self.sensor_readings,
        })

        time.sleep(1)

    def run(self):
        """Execute the mission simulation."""
        try:
            self.status = "running"
            self.add_log(f"🚀 Mission started: {self.mission_type.upper()} on {self.dataset['name']}")
            self.broadcast_update("mission_started", {
                "mission_id": self.mission_id,
                "dataset": self.dataset["name"],
                "mission_type": self.mission_type,
            })

            # Simulate each location
            for idx, location_data in enumerate(self.dataset["locations"]):
                if self.battery_level < 5.0:
                    self.add_log("⚠️  Mission halted: Low battery")
                    break

                self.simulate_location(idx, location_data)
                time.sleep(0.5)

            self.status = "completed"
            self.progress = 100
            self.add_log(f"✅ Mission complete! Collected {len(self.samples_found)} samples")

            self.broadcast_update("mission_completed", {
                "mission_id": self.mission_id,
                "samples_collected": len(self.samples_found),
                "battery_remaining": self.battery_level,
                "duration": (datetime.now() - self.start_time).total_seconds(),
            })

        except Exception as e:
            self.status = "error"
            self.add_log(f"❌ Error: {str(e)}")
            self.broadcast_update("mission_error", {
                "mission_id": self.mission_id,
                "error": str(e),
            })


# API Endpoints

@app.route("/")
def index():
    """Serve main dashboard."""
    return render_template("index.html")


@app.route("/api/datasets", methods=["GET"])
def get_datasets():
    """List available datasets."""
    datasets = {
        "simple": {
            "key": "simple",
            "name": "Simple Survey",
            "description": "Flat terrain, isolated rocks",
            "difficulty": "Easy",
            "locations": 5
        },
        "complex": {
            "key": "complex",
            "name": "Complex Terrain",
            "description": "Hills, slopes, hazards",
            "difficulty": "Hard",
            "locations": 8
        },
        "crater": {
            "key": "crater",
            "name": "Crater Exploration",
            "description": "Subsurface drilling targets",
            "difficulty": "Medium",
            "locations": 6
        }
    }
    return jsonify(list(datasets.values()))


@app.route("/api/missions", methods=["GET"])
def get_mission_types():
    """List available mission types."""
    missions = [
        {
            "key": "explore",
            "name": "Exploration",
            "description": "Autonomous terrain survey"
        },
        {
            "key": "sample_collection",
            "name": "Sample Collection",
            "description": "Focused sampling mission"
        },
        {
            "key": "hazard_assessment",
            "name": "Hazard Assessment",
            "description": "Risk evaluation survey"
        }
    ]
    return jsonify(missions)


@app.route("/api/missions/start", methods=["POST"])
def start_mission():
    """Start a new mission."""
    data = request.get_json()

    dataset_key = data.get("dataset", "simple")
    mission_type = data.get("mission_type", "explore")
    use_llm = data.get("use_llm", False)

    mission_id = str(uuid.uuid4())
    simulator = MissionSimulator(mission_id, dataset_key, mission_type, use_llm)

    active_missions[mission_id] = simulator

    # Run mission in background thread
    thread = threading.Thread(target=simulator.run, daemon=True)
    mission_threads[mission_id] = thread
    thread.start()

    return jsonify({
        "mission_id": mission_id,
        "status": "started",
        "dataset": simulator.dataset["name"],
        "mission_type": mission_type
    })


@app.route("/api/missions/<mission_id>/status", methods=["GET"])
def get_mission_status(mission_id):
    """Get status of a running mission."""
    if mission_id not in active_missions:
        return jsonify({"error": "Mission not found"}), 404

    mission = active_missions[mission_id]
    return jsonify({
        "mission_id": mission_id,
        "status": mission.status,
        "progress": mission.progress,
        "current_location": mission.current_location,
        "rover_position": mission.rover_position,
        "battery_level": mission.battery_level,
        "samples_count": len(mission.samples_found),
        "sensor_readings": mission.sensor_readings,
        "start_time": mission.start_time.isoformat(),
        "elapsed_seconds": (datetime.now() - mission.start_time).total_seconds(),
    })


@app.route("/api/missions/<mission_id>/report", methods=["GET"])
def get_mission_report(mission_id):
    """Get complete mission report."""
    if mission_id not in active_missions:
        return jsonify({"error": "Mission not found"}), 404

    mission = active_missions[mission_id]

    # Rank samples by scientific value
    ranked_samples = sorted(
        mission.samples_found,
        key=lambda x: x["confidence"],
        reverse=True
    )[:10]

    return jsonify({
        "mission_id": mission_id,
        "status": mission.status,
        "dataset": mission.dataset["name"],
        "mission_type": mission.mission_type,
        "start_time": mission.start_time.isoformat(),
        "duration_seconds": (datetime.now() - mission.start_time).total_seconds(),
        "samples_collected": len(mission.samples_found),
        "battery_remaining": mission.battery_level,
        "locations_explored": mission.current_location,
        "top_samples": ranked_samples,
        "final_sensor_readings": mission.sensor_readings,
        "log_entries": mission.log_entries,
    })


@app.route("/api/missions/<mission_id>/logs", methods=["GET"])
def get_mission_logs(mission_id):
    """Get mission log entries."""
    if mission_id not in active_missions:
        return jsonify({"error": "Mission not found"}), 404

    mission = active_missions[mission_id]
    return jsonify({
        "mission_id": mission_id,
        "logs": mission.log_entries
    })


@app.route("/api/missions/active", methods=["GET"])
def get_active_missions():
    """List all active missions."""
    missions = []
    for mission_id, mission in active_missions.items():
        missions.append({
            "mission_id": mission_id,
            "status": mission.status,
            "progress": mission.progress,
            "dataset": mission.dataset["name"],
            "mission_type": mission.mission_type,
            "samples_found": len(mission.samples_found),
        })
    return jsonify(missions)


# ── Manual Rover Controller ───────────────────────────────────────────────────
import math as _math

COLLECT_RADIUS = 3.0   # metres — how close the rover must be to grab a sample

_rover_state = {
    "x": 0.0, "y": 0.0,
    "heading": 0.0,   # degrees, 0 = north/up
    "speed": 2.0,     # metres per step
    "battery": 100.0,
    "odometer": 0.0,
    "trail": [],      # list of [x, y] visited
    "hazard_zones": [ # static hazard zones on the map
        {"x": 15, "y": 10, "radius": 5, "type": "radiation",  "label": "High Radiation Zone"},
        {"x": -12, "y": 18, "radius": 4, "type": "debris",    "label": "Debris Field"},
        {"x": 5,  "y": -15, "radius": 6, "type": "slope",     "label": "Steep Slope"},
        {"x": -20, "y": -8, "radius": 3, "type": "crater",    "label": "Crater Rim"},
    ],
    "sample_sites": [   # rock/sample locations to collect
        {"id": "S1", "x": 8,   "y": 6,   "type": "basalt",      "value": 0.92, "collected": False},
        {"id": "S2", "x": -6,  "y": 9,   "type": "olivine",     "value": 0.88, "collected": False},
        {"id": "S3", "x": 12,  "y": -4,  "type": "anorthosite", "value": 0.95, "collected": False},
        {"id": "S4", "x": -14, "y": -3,  "type": "ilmenite",    "value": 0.81, "collected": False},
        {"id": "S5", "x": 3,   "y": 13,  "type": "breccia",     "value": 0.76, "collected": False},
        {"id": "S6", "x": -9,  "y": -12, "type": "regolith",    "value": 0.64, "collected": False},
        {"id": "S7", "x": 17,  "y": 2,   "type": "pyroxene",    "value": 0.89, "collected": False},
        {"id": "S8", "x": -2,  "y": -8,  "type": "feldspar",    "value": 0.72, "collected": False},
    ],
    "collected_samples": [],
    "alerts": [],
}


def _nearest_sample():
    """Return (site, distance) of the closest uncollected sample, or (None, inf)."""
    rx, ry = _rover_state["x"], _rover_state["y"]
    best, best_d = None, float("inf")
    for s in _rover_state["sample_sites"]:
        if s["collected"]:
            continue
        d = _math.sqrt((rx - s["x"])**2 + (ry - s["y"])**2)
        if d < best_d:
            best, best_d = s, d
    return best, best_d


def _bearing_to_compass(bearing):
    """Convert a 0-360° bearing (0=N, 90=E) to an 8-point compass label + arrow."""
    dirs = [
        ("N", "↑"), ("NE", "↗"), ("E", "→"), ("SE", "↘"),
        ("S", "↓"), ("SW", "↙"), ("W", "←"), ("NW", "↖"),
    ]
    idx = int((bearing + 22.5) % 360 / 45)
    return dirs[idx]


def _scan_category(targets, scale):
    """
    Given a list of (x, y, weight) targets, compute the probability that more
    are nearby and the dominant compass direction toward them.

    Returns dict with probability (0-1), bearing, compass, arrow, nearest distance.
    """
    rx, ry = _rover_state["x"], _rover_state["y"]
    if not targets:
        return None

    vx, vy = 0.0, 0.0          # weighted direction vector
    total_score = 0.0          # field strength (drives probability)
    nearest_d = float("inf")
    count_near = 0

    for tx, ty, w in targets:
        dx, dy = tx - rx, ty - ry
        d = _math.sqrt(dx*dx + dy*dy)
        if d < 0.01:
            d = 0.01
        # Inverse-distance influence (a "scent" gradient)
        influence = w * _math.exp(-d / scale)
        vx += influence * (dx / d)
        vy += influence * (dy / d)
        total_score += influence
        nearest_d = min(nearest_d, d)
        if d <= scale:
            count_near += 1

    # Probability of "more nearby" — saturates as field strength grows
    probability = 1.0 - _math.exp(-total_score)

    # Direction confidence: how aligned the targets are (0 = scattered)
    mag = _math.sqrt(vx*vx + vy*vy)
    bearing = (_math.degrees(_math.atan2(vx, vy)) % 360) if mag > 1e-6 else 0.0
    compass, arrow = _bearing_to_compass(bearing)

    return {
        "probability": round(probability, 3),
        "bearing": round(bearing, 1),
        "compass": compass,
        "arrow": arrow,
        "nearest_m": round(nearest_d, 1),
        "count_near": count_near,
    }


def _field_scan():
    """
    Directional probability scan: for samples, debris/terrain hazards, and
    radiation, estimate the chance of finding more and which way it lies.
    """
    results = {}

    # 1. Samples — uncollected sites, weighted by scientific value
    sample_targets = [(s["x"], s["y"], 0.5 + s["value"])
                      for s in _rover_state["sample_sites"] if not s["collected"]]
    results["samples"] = _scan_category(sample_targets, scale=12.0)

    # 2. Debris / terrain hazards (debris, crater, slope zones)
    debris_targets = [(z["x"], z["y"], z["radius"] / 3.0)
                      for z in _rover_state["hazard_zones"]
                      if z["type"] in ("debris", "crater", "slope")]
    results["debris"] = _scan_category(debris_targets, scale=10.0)

    # 3. Radiation fields — radiation zones, amplified by the live cosmic dose
    rad_now = _current_env_row().get("radiation", 0)
    rad_boost = max(1.0, rad_now / 60.0)   # lunar baseline ~60 µSv/h
    rad_targets = [(z["x"], z["y"], (z["radius"] / 3.0) * rad_boost)
                   for z in _rover_state["hazard_zones"] if z["type"] == "radiation"]
    results["radiation"] = _scan_category(rad_targets, scale=10.0)
    if results["radiation"]:
        results["radiation"]["live_usv_h"] = round(rad_now, 1)

    return results


def _check_rover_hazards():
    """Return list of active hazard alerts for current rover position."""
    alerts = []
    rx, ry = _rover_state["x"], _rover_state["y"]
    for zone in _rover_state["hazard_zones"]:
        dist = _math.sqrt((rx - zone["x"])**2 + (ry - zone["y"])**2)
        if dist < zone["radius"] * 1.5:          # warn when approaching
            severity = "DANGER" if dist < zone["radius"] else "WARNING"
            alerts.append({
                "type": zone["type"],
                "label": zone["label"],
                "severity": severity,
                "distance_m": round(dist, 1),
            })
    # live radiation check from CSV — lunar baseline cosmic dose is ~50-75 µSv/h,
    # solar particle events push it higher
    row = _current_env_row()
    rad = row.get("radiation", 0)
    if rad > 120:
        alerts.append({"type": "radiation", "label": "Solar Particle Event — High Radiation",
                       "severity": "DANGER", "value": rad, "unit": "µSv/h"})
    elif rad > 90:
        alerts.append({"type": "radiation", "label": "Elevated Cosmic Radiation",
                       "severity": "WARNING", "value": rad, "unit": "µSv/h"})
    if row.get("pm25", 0) > 8:
        alerts.append({"type": "dust", "label": "Regolith Dust Disturbance",
                       "severity": "WARNING", "value": row["pm25"], "unit": "µg/m³"})
    return alerts


@app.route("/api/rover/state", methods=["GET"])
def get_rover_state():
    s = _rover_state
    alerts = _check_rover_hazards()
    live = _current_env_row()
    return jsonify({**s, "alerts": alerts,
                    "live_radiation": live.get("radiation"),
                    "live_pm25": live.get("pm25"),
                    "hazard_zones": s["hazard_zones"],
                    "nearest_sample": _nearest_sample_info(),
                    "field_scan": _field_scan()})


@app.route("/api/rover/scan", methods=["GET"])
def rover_scan():
    """Directional probability scan for samples / debris / radiation."""
    return jsonify({"field_scan": _field_scan(),
                    "position": {"x": _rover_state["x"], "y": _rover_state["y"]}})


@app.route("/api/rover/move", methods=["POST"])
def move_rover():
    data = request.get_json()
    direction = data.get("direction", "").lower()
    steps = int(data.get("steps", 1))
    speed = _rover_state["speed"]

    if direction == "reset":
        _rover_state.update({"x": 0.0, "y": 0.0, "heading": 0.0,
                              "battery": 100.0, "odometer": 0.0, "trail": [], "alerts": []})
        return jsonify({"ok": True, **_rover_state})

    # Absolute, screen-aligned 8-directional movement (like a top-down game d-pad).
    # +y = up/north, +x = right/east. Independent of which way the rover faces.
    INV = 1 / _math.sqrt(2)
    dir_map = {
        "forward":       ( 0.0,  1.0),   # N
        "back":          ( 0.0, -1.0),   # S
        "left":          (-1.0,  0.0),   # W
        "right":         ( 1.0,  0.0),   # E
        "forward-left":  (-INV,  INV),   # NW
        "forward-right": ( INV,  INV),   # NE
        "back-left":     (-INV, -INV),   # SW
        "back-right":    ( INV, -INV),   # SE
    }
    if direction not in dir_map:
        return jsonify({"error": "Unknown direction"}), 400

    ux, uy = dir_map[direction]
    dx = ux * speed * steps
    dy = uy * speed * steps

    # Point the rover toward its travel direction (heading: 0°=N, 90°=E)
    _rover_state["heading"] = round((_math.degrees(_math.atan2(ux, uy))) % 360, 1)

    _rover_state["x"] = round(_rover_state["x"] + dx, 2)
    _rover_state["y"] = round(_rover_state["y"] + dy, 2)
    dist = _math.sqrt(dx**2 + dy**2)
    _rover_state["odometer"] = round(_rover_state["odometer"] + dist, 2)
    _rover_state["battery"] = max(0, round(_rover_state["battery"] - dist * 0.05, 2))
    _rover_state["trail"].append([_rover_state["x"], _rover_state["y"]])
    if len(_rover_state["trail"]) > 200:
        _rover_state["trail"] = _rover_state["trail"][-200:]

    alerts = _check_rover_hazards()
    _rover_state["alerts"] = alerts
    payload = {**_rover_state, "alerts": alerts,
               "nearest_sample": _nearest_sample_info(),
               "field_scan": _field_scan()}
    socketio.emit("rover_moved", payload, to="/")
    return jsonify(payload)


def _nearest_sample_info():
    """Compact info about the closest uncollected sample, for the UI."""
    site, dist = _nearest_sample()
    if site is None:
        return None
    return {
        "id": site["id"], "type": site["type"], "value": site["value"],
        "x": site["x"], "y": site["y"],
        "distance": round(dist, 1),
        "in_range": dist <= COLLECT_RADIUS,
    }


@app.route("/api/rover/collect", methods=["POST"])
def collect_sample():
    """Collect the nearest uncollected sample if the rover is close enough."""
    site, dist = _nearest_sample()
    if site is None:
        return jsonify({"ok": False, "message": "All samples collected!"}), 200
    if dist > COLLECT_RADIUS:
        return jsonify({"ok": False,
                        "message": f"Nearest sample {site['id']} is {dist:.1f} m away — move within {COLLECT_RADIUS:.0f} m.",
                        "nearest_sample": _nearest_sample_info()}), 200

    site["collected"] = True
    _rover_state["battery"] = max(0, round(_rover_state["battery"] - 2.0, 2))  # gripper power
    record = {"id": site["id"], "type": site["type"], "value": site["value"],
              "x": site["x"], "y": site["y"], "confidence": site["value"]}
    _rover_state["collected_samples"].append(record)

    payload = {**_rover_state, "alerts": _check_rover_hazards(),
               "nearest_sample": _nearest_sample_info(),
               "field_scan": _field_scan()}
    socketio.emit("rover_moved", payload, to="/")
    return jsonify({"ok": True,
                    "message": f"Collected {site['type'].title()} ({site['id']}) — value {site['value']:.2f}",
                    "sample": record, **payload})


@app.route("/api/rover/rotate", methods=["POST"])
def rotate_rover():
    data = request.get_json()
    degrees = float(data.get("degrees", 45))
    _rover_state["heading"] = (_rover_state["heading"] + degrees) % 360
    payload = {**_rover_state, "alerts": _check_rover_hazards(),
               "nearest_sample": _nearest_sample_info(), "field_scan": _field_scan()}
    socketio.emit("rover_moved", payload, to="/")
    return jsonify(payload)


@app.route("/api/rover/speed", methods=["POST"])
def set_speed():
    data = request.get_json()
    _rover_state["speed"] = max(0.5, min(10.0, float(data.get("speed", 2.0))))
    return jsonify({"speed": _rover_state["speed"]})


# Live sensor readings endpoint

@app.route("/api/sensors/live", methods=["GET"])
def get_live_readings():
    """Return the current env-probe row (updates every 2 s)."""
    row = _current_env_row()
    if not row:
        return jsonify({"error": "Env-probe CSV not loaded"}), 503
    return jsonify(row)


# Sensor Data Endpoints

@app.route("/api/sensors", methods=["GET"])
def get_available_sensors():
    """List available sensors and their capabilities."""
    sensors = {}
    for sensor_type in SensorDataLoader.get_all_sensors():
        info = SensorDataLoader.get_sensor_info(sensor_type)
        sensors[sensor_type] = {
            "name": info["name"],
            "description": info["description"],
            "capabilities": info["capabilities"],
            "uses": info["uses"],
        }
    return jsonify(sensors)


@app.route("/api/sensors/<sensor_type>/data", methods=["GET"])
def get_sensor_data(sensor_type):
    """Load and return sensor data summary."""
    if sensor_type == "radar":
        data = SensorDataLoader.load_radar_data()
    elif sensor_type == "thermal":
        data = SensorDataLoader.load_thermal_data()
    elif sensor_type == "lidar":
        data = SensorDataLoader.load_lidar_data()
    else:
        return jsonify({"error": "Unknown sensor type"}), 404

    if not data:
        return jsonify({"error": "Sensor data not found"}), 404

    return jsonify({
        "sensor": data["sensor"],
        "name": data["name"],
        "summary": data["summary"],
        "available_analyses": SensorDataLoader.SENSOR_SPECS[sensor_type].get("capabilities", []),
    })


@app.route("/api/sensors/<sensor_type>/analyze", methods=["POST"])
def analyze_sensor_data(sensor_type):
    """Perform analysis on sensor data."""
    data = request.get_json()
    analysis_type = data.get("analysis_type")

    if not analysis_type:
        return jsonify({"error": "analysis_type required"}), 400

    result = SensorDataLoader.perform_analysis(sensor_type, analysis_type)

    if "error" in result:
        return jsonify(result), 400

    return jsonify({
        "sensor": sensor_type,
        "analysis": result,
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/api/sensors/<sensor_type>/capabilities", methods=["GET"])
def get_sensor_capabilities(sensor_type):
    """Get what a sensor can do."""
    info = SensorDataLoader.get_sensor_info(sensor_type)
    if not info:
        return jsonify({"error": "Unknown sensor type"}), 404

    return jsonify({
        "sensor": sensor_type,
        "name": info["name"],
        "description": info["description"],
        "capabilities": info["capabilities"],
        "practical_uses": info["uses"],
        "available_tests": [
            {
                "name": name,
                "description": f"Run {name}",
                "type": test_type,   # exact key perform_analysis() dispatches on
            }
            for test_type, name in SensorDataLoader.SENSOR_TESTS.get(sensor_type, [])
        ],
    })


# WebSocket Events

@socketio.on("connect")
def handle_connect():
    """Handle client connection."""
    emit("connected", {"data": "Connected to Mission Control API"})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection."""
    pass


@socketio.on("request_update")
def handle_update_request(data):
    """Handle real-time update requests."""
    mission_id = data.get("mission_id")
    if mission_id in active_missions:
        mission = active_missions[mission_id]
        emit("mission_update", {
            "mission_id": mission_id,
            "status": mission.status,
            "progress": mission.progress,
            "current_location": mission.current_location,
            "rover_position": mission.rover_position,
            "battery_level": mission.battery_level,
            "samples_count": len(mission.samples_found),
            "sensor_readings": mission.sensor_readings,
        })


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
