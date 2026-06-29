# 🚀 Quick Start Guide - Rover Web Simulation

## Installation & Launch (2 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start the Server
```bash
python run_web.py
```

You should see:
```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║          🚀 Rover Mission Control Web Server 🚀          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

✓ Flask dependencies installed
✓ All dependencies available

Starting server...

============================================================
🌐 Server running at: http://localhost:5000
📊 Open this URL in your web browser to access Mission Control
============================================================
```

### Step 3: Open in Browser
Click or copy this link to your browser: **http://localhost:5000**

---

## Using the Dashboard

### 1️⃣ Select Mission Parameters
- **Dataset**: Choose terrain type (Simple, Complex, or Crater)
- **Mission Type**: Select exploration, sampling, or hazard assessment
- **LLM**: Toggle Claude AI for advanced reasoning (optional)

### 2️⃣ Click "Start Mission"
- Mission begins immediately
- Real-time updates via WebSocket

### 3️⃣ Monitor Mission
Watch the live updates:
- **Progress bar** - Mission completion percentage
- **Terrain map** - Rover position and movement (center = base, green dot = rover)
- **Sensor readings** - Current environmental data
- **Mission log** - All events with timestamps
- **Samples** - Rock detections and classifications

### 4️⃣ View Report
After mission completes:
- Click "View Full Report" button
- See comprehensive mission analysis
- Review top scientific samples
- Check final sensor readings
- Download or save report as needed

---

## Features by Section

### 🎮 Left Panel - Mission Control
```
┌─────────────────────┐
│ Dataset Selection   │  Choose test environment
│ Mission Type        │  Choose mission objective
│ Enable LLM          │  Toggle AI reasoning
│ Start Mission       │  Launch simulation
│ Active Missions     │  Track multiple runs
└─────────────────────┘
```

### 📊 Center Panel - Visualization
```
┌─────────────────────┐
│ Mission Status      │  Progress, battery, location
│ Terrain Map         │  2D rover position tracker
│ Sensor Readings     │  Live environment data
└─────────────────────┘
```

### 📝 Right Panel - Details
```
┌─────────────────────┐
│ Mission Log         │  Real-time event log
│ Samples Collected   │  Rock detections
│ View Report         │  Full mission analysis
└─────────────────────┘
```

---

## Example Workflow

**1. Simple Survey (Perfect for First Test)**
```
Dataset:      Simple Survey
Mission Type: Exploration
LLM:          Off (for speed)
```

Expected: ~20-30 seconds, 5-10 samples collected

**2. Complex Terrain (Advanced)**
```
Dataset:      Complex Terrain
Mission Type: Sample Collection
LLM:          On (better decisions)
```

Expected: ~40-60 seconds, 15-20 samples, more interesting data

**3. Crater Exploration (Scientific)**
```
Dataset:      Crater Exploration
Mission Type: Hazard Assessment
LLM:          On
```

Expected: ~30-40 seconds, subsurface detection enabled

---

## Sensor Data Explained

### Environmental Sensors
| Sensor | Range | Units | What It Measures |
|--------|-------|-------|------------------|
| 🌡️ Temperature | 0-30°C | °C | Air temperature |
| 💧 Humidity | 0-100% | % | Moisture level |
| ⊡ Pressure | 990-1020 | hPa | Atmospheric pressure |
| ☢️ Radiation | 0-0.2 | mSv/h | Cosmic radiation exposure |
| ⚡ Conductivity | 0-2 | mS/cm | Soil electrical conductivity |
| 📏 Depth | 0-15 | cm | Soil sampling depth |

### Sample Classification
- **ID**: Unique sample identifier
- **Type**: Basalt, Olivine, Anorthosite, etc.
- **Confidence**: 0-100% detection confidence
- **XRD/XRF**: Mineral and elemental composition
- **Depth**: Soil core sampling depth
- **pH**: Regolith acidity measurement

---

## Real-Time Updates

### What Updates in Real-Time?
✅ Rover position on terrain map  
✅ Mission progress bar  
✅ Battery level  
✅ Sensor readings  
✅ Mission log entries  
✅ Sample count  

### Update Frequency
- **WebSocket**: 500ms (immediate)
- **Polling**: 1-2 seconds (periodic sync)
- **UI Refresh**: ~60fps (smooth animations)

---

## Troubleshooting

### "Connection refused" or "Cannot connect"
```
❌ Issue: Server not running
✅ Fix: Run `python run_web.py` in the project directory
```

### "Port 5000 already in use"
```
❌ Issue: Another process using port 5000
✅ Fix (Windows):
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F

✅ Fix (Mac/Linux):
   lsof -ti:5000 | xargs kill -9
```

### "Missing modules" or import errors
```
❌ Issue: Dependencies not installed
✅ Fix: pip install -r requirements.txt
```

### "WebSocket connection failed"
```
❌ Issue: Browser-server communication problem
✅ Fix: 
   - Check browser console (F12 → Console)
   - Verify firewall allows localhost
   - Restart browser and server
   - Try different browser
```

### Slow performance or lag
```
❌ Issue: High CPU usage or slow browser
✅ Fix:
   - Close other applications
   - Disable LLM (reduces computation)
   - Use simpler dataset
   - Try Chrome/Edge instead of Firefox
```

---

## File Structure

```
AI-Lab-Robot/
├── app.py                  # Flask API backend
├── run_web.py             # Quick start script
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html         # Web dashboard
├── static/
│   ├── app.js            # WebSocket & UI logic
│   └── style.css         # Dark theme styling
├── rover/                # Rover hardware simulation
├── sensors/              # Sensor simulators
├── ai/                   # AI/ML components
├── data/                 # Dataset handlers
└── WEB_APP_README.md     # Full documentation
```

---

## Next Steps

### 🔧 Customize
- Edit `app.py` to add new datasets
- Modify `static/style.css` for different theme
- Extend `static/app.js` for new features

### 🚀 Extend
- Add 3D visualization with Three.js
- Integrate real rover hardware
- Add multi-rover coordination
- Create mission templates

### 📊 Analyze
- Export mission data
- Create analytics dashboard
- Build ML models from collected data
- Train sample classifiers

---

## API Endpoints (Advanced Users)

If you want to programmatically control missions:

```bash
# Start a mission
curl -X POST http://localhost:5000/api/missions/start \
  -H "Content-Type: application/json" \
  -d '{"dataset":"simple","mission_type":"explore"}'

# Get mission status
curl http://localhost:5000/api/missions/<mission_id>/status

# Get full report
curl http://localhost:5000/api/missions/<mission_id>/report

# List datasets
curl http://localhost:5000/api/datasets
```

---

## Tips & Tricks

🎯 **Fast Testing**: Use Simple Survey + Exploration (no LLM)

🔬 **Rich Data**: Use Crater + Sample Collection (with LLM for analysis)

🎓 **Learning**: Watch logs while mission runs to understand rover behavior

📈 **Analysis**: Compare multiple missions to see dataset differences

💾 **Archiving**: Save reports before closing browser

---

## Getting Help

1. **Check WEB_APP_README.md** - Full feature documentation
2. **Review ROVER_SPECIFICATION.md** - Technical specs
3. **Check browser console** - F12 → Console tab for errors
4. **Server logs** - Check terminal running `python run_web.py`

---

**Ready to explore? Click "Start Mission" on the dashboard!** 🚀
