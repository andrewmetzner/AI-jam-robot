# 🚀 Rover Mission Control Web App

A modern web-based simulation dashboard for the AI-Lab autonomous rover system.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Web Server

```bash
python run_web.py
```

Or directly:

```bash
python app.py
```

### 3. Open in Browser

Navigate to: **http://localhost:5000**

## Features

### 🎮 Mission Control Panel
- **Dataset Selection**: Choose from multiple terrain datasets (Simple Survey, Complex Terrain, Crater Exploration)
- **Mission Types**: Select exploration, sample collection, or hazard assessment missions
- **LLM Integration**: Toggle Claude AI reasoning for advanced decision-making
- **Active Missions**: View and manage multiple concurrent missions

### 📊 Real-time Visualization
- **Mission Status**: Progress tracking, battery level, location, samples collected
- **Terrain Map**: 2D visualization of rover position and movement
- **Sensor Readings**: Live telemetry from:
  - 🌡️ Temperature Probe
  - 💧 Humidity Sensor
  - ⊡ Barometric Pressure Sensor
  - ☢️ Cosmic Radiation Detector
  - ⚡ Electrical Conductivity Probe
  - 📏 Depth Sensor

### 📝 Mission Logs
- Real-time activity logging with timestamps
- Event tracking (location arrivals, sensor anomalies, samples found, battery status)
- Color-coded status indicators

### 🔬 Sample Analysis
- Automatic detection and classification of rock samples
- Confidence scoring
- Elemental composition tracking:
  - X-Ray Diffraction (XRD) – Mineral Identification
  - X-Ray Fluorescence (XRF) – Elemental Composition
  - Ground Penetrating Radar (GPR) – Subsurface detection
  - pH measurement
  - Core sampling (0-15 cm depth)

### 📋 Mission Reports
- Comprehensive post-mission analysis
- Top scientifically valuable samples ranked by confidence
- Final sensor readings and environmental data
- Complete activity log
- Statistical summary (duration, battery usage, exploration coverage)

## Architecture

### Backend (Flask API)

**Endpoints:**

- `GET /api/datasets` - List available datasets
- `GET /api/missions` - List mission types
- `POST /api/missions/start` - Start new mission
- `GET /api/missions/<id>/status` - Get mission status
- `GET /api/missions/<id>/report` - Get mission report
- `GET /api/missions/<id>/logs` - Get mission logs
- `GET /api/missions/active` - List all active missions

**WebSocket Events:**

- `connect` - Client connects
- `disconnect` - Client disconnects
- `mission_update` - Real-time mission status
- `mission_started` - Mission initialization
- `mission_completed` - Mission finished
- `mission_error` - Error occurred
- `log_entry` - New log message

### Frontend (HTML/CSS/JavaScript)

- **index.html** - Main dashboard layout
- **style.css** - Modern dark-themed UI with responsive design
- **app.js** - WebSocket client, API integration, real-time updates

### Simulation Engine

- **MissionSimulator** class handles autonomous rover simulation
- Mock datasets for different terrain types
- Sensor data generation based on location
- Sample detection and analysis
- Battery drain simulation

## Available Datasets

### 1. Simple Survey (Easy)
- 5 locations on flat terrain
- 2 rock samples per location
- Minimal hazards
- Good for testing basic functionality

### 2. Complex Terrain (Hard)
- 8 locations with hills and slopes
- 3 rock samples per location
- Crater hazards
- Higher difficulty navigation

### 3. Crater Exploration (Medium)
- 6 locations in crater region
- Subsurface detection targets
- Ground Penetrating Radar opportunities
- Deep core sampling sites

## Sensor Data Types

### Robotics Sensors
- **Temperature Probe**: Environmental temperature monitoring
- **Humidity Probe**: Moisture level detection
- **Barometric Pressure Sensor**: Altitude and pressure data
- **Air Quality Sensor**: Light absorbance & scattering measurement
- **Cosmic Radiation Detector**: High-energy particle monitoring
- **Electrical Conductivity Probe**: Soil/regolith conductivity

### Scientific Instruments
- **XRD (X-Ray Diffraction)**: Mineral phase identification
- **XRF (X-Ray Fluorescence)**: Elemental composition analysis
- **GPR (Ground Penetrating Radar)**: Subsurface structure detection
- **pH Probe**: Regolith acidity/alkalinity measurement
- **Soil Core Sampler**: 0-15 cm depth sampling
- **Gas Syringe Sampler**: Atmospheric and soil gas collection

## API Response Examples

### Mission Start
```json
{
  "mission_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started",
  "dataset": "Simple Survey",
  "mission_type": "explore"
}
```

### Mission Status
```json
{
  "mission_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 45.5,
  "current_location": 3,
  "rover_position": [6.0, 0.0],
  "battery_level": 67.5,
  "samples_count": 5,
  "sensor_readings": {
    "temperature": 18.5,
    "humidity": 52.0,
    "pressure": 1012.25,
    "radiation": 0.065,
    "conductivity": 0.95,
    "depth_average": 5.0
  }
}
```

### Mission Report
```json
{
  "mission_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "samples_collected": 10,
  "battery_remaining": 12.5,
  "locations_explored": 5,
  "duration_seconds": 45,
  "top_samples": [
    {
      "id": "rock_0_0",
      "type": "olivine",
      "confidence": 0.92,
      "location": 0
    }
  ],
  "log_entries": [...]
}
```

## Development

### Modify Mission Parameters
Edit mock dataset definitions in `app.py` `MissionSimulator._create_mock_dataset()`:

```python
datasets = {
    "custom": {
        "name": "Custom Dataset",
        "num_locations": 10,
        "locations": [...]
    }
}
```

### Add New Sensors
Extend sensor readings in `simulate_location()`:

```python
self.sensor_readings = {
    "temperature": ...,
    "humidity": ...,
    "new_sensor": value,  # Add here
    ...
}
```

### Customize UI
- Modify `templates/index.html` for layout changes
- Update `static/style.css` for styling
- Edit `static/app.js` for functionality

## Troubleshooting

### Port Already in Use
If port 5000 is already in use:
```bash
# On Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# On macOS/Linux
lsof -ti:5000 | xargs kill -9
```

### WebSocket Connection Failed
- Ensure server is running
- Check browser console for connection errors
- Verify firewall settings allow localhost connections

### Missing Modules
Run: `pip install -r requirements.txt`

### CORS Issues
CORS is configured in `app.py` with `CORS(app)`

## Performance Notes

- Simulations run in background threads (non-blocking)
- WebSocket updates throttled to 500ms for efficiency
- UI updates via polling (1-2 second intervals)
- Canvas rendering optimized for 60fps

## Future Enhancements

- [ ] 3D terrain visualization with Three.js
- [ ] Real-time satellite/aerial imagery integration
- [ ] Advanced ML-based sample classification
- [ ] Multi-rover coordination
- [ ] Historical mission archive
- [ ] Advanced analytics and charts
- [ ] Customizable mission parameters
- [ ] Export mission data to CSV/JSON

## License

Part of the AI-Lab Rover project. See main repository for details.

---

**Questions or issues?** Check the main project README or API documentation.
