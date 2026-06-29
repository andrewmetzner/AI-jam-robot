// Rover Mission Control Web App
const API_BASE = 'http://localhost:5000';
let socket;
let activeMissionId = null;
let missionData = {};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Rover Mission Control Web App');

    initializeWebSocket();
    setupEventListeners();
    drawTerrainMap();
});

// WebSocket Setup
function initializeWebSocket() {
    socket = io(API_BASE, {
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        reconnectionAttempts: 5
    });

    socket.on('connect', () => {
        console.log('Connected to server');
        updateConnectionStatus(true);
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updateConnectionStatus(false);
    });

    socket.on('mission_update', (data) => {
        updateMissionStatus(data);
    });

    socket.on('mission_started', (data) => {
        console.log('Mission started:', data);
        addLog(`🚀 Mission started: ${data.mission_type.toUpperCase()}`);
    });

    socket.on('mission_completed', (data) => {
        console.log('Mission completed:', data);
        document.getElementById('view-report-btn').style.display = 'block';
        addLog(`✅ Mission complete! Collected ${data.samples_collected} samples`);
    });

    socket.on('mission_error', (data) => {
        console.error('Mission error:', data);
        addLog(`❌ Error: ${data.error}`);
    });

    socket.on('log_entry', (data) => {
        addLog(data.message);
    });

    socket.on('connected', (data) => {
        console.log(data.data);
        fetchLiveReadings();
    });

    socket.on('live_sensor', (data) => {
        updateSensorDisplay(data);
    });

    socket.on('rover_moved', (data) => {
        applyRoverState(data);
    });
}

async function fetchLiveReadings() {
    try {
        const res = await fetch(`${API_BASE}/api/sensors/live`);
        if (!res.ok) return;
        const data = await res.json();
        updateSensorDisplay(data);
    } catch (e) {
        // server not ready yet — will catch up on next push
    }
}

// ── Tab switching ─────────────────────────────────────
let _unreadLogs = 0;

function switchTab(name) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.toggle('active', p.id === `tab-${name}`));
    if (name === 'logs') {
        _unreadLogs = 0;
        const btn = document.querySelector('[data-tab="logs"]');
        if (btn) btn.innerHTML = 'Mission Logs';
    }
}

function clearLog() {
    document.getElementById('logs-container').innerHTML = '<p class="placeholder">Log cleared</p>';
}

// Event Listeners
function setupEventListeners() {
    document.getElementById('start-mission-btn').addEventListener('click', startMission);
    document.getElementById('view-report-btn').addEventListener('click', viewReport);
    document.getElementById('sensor-select').addEventListener('change', handleSensorChange);
    document.getElementById('run-test-btn').addEventListener('click', runSensorTest);
    document.querySelector('.close').addEventListener('click', closeReportModal);
    window.addEventListener('click', (e) => {
        if (e.target === document.getElementById('report-modal')) closeReportModal();
    });
    // Tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
}

// Mission Control Functions
async function startMission() {
    const dataset = document.getElementById('dataset-select').value;
    const mission_type = document.getElementById('mission-select').value;
    const use_llm = document.getElementById('llm-toggle').checked;

    const btn = document.getElementById('start-mission-btn');
    btn.disabled = true;
    btn.textContent = 'Starting...';

    try {
        const response = await fetch(`${API_BASE}/api/missions/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dataset, mission_type, use_llm })
        });

        const data = await response.json();
        activeMissionId = data.mission_id;
        missionData[activeMissionId] = data;

        console.log('Mission started:', data);

        // Clear previous data
        document.getElementById('logs-container').innerHTML = '';
        document.getElementById('samples-container').innerHTML = '<p class="placeholder">No samples collected yet</p>';
        document.getElementById('view-report-btn').style.display = 'none';

        // Highlight active mission
        updateActiveMissionsList();

        // Start polling for updates
        pollMissionStatus(activeMissionId);

    } catch (error) {
        console.error('Error starting mission:', error);
        alert('Error starting mission: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Start Mission';
    }
}

function pollMissionStatus(missionId) {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/missions/${missionId}/status`);
            const data = await response.json();

            updateMissionStatus(data);

            if (data.status === 'completed' || data.status === 'error') {
                clearInterval(pollInterval);
            }
        } catch (error) {
            console.error('Error polling mission status:', error);
            clearInterval(pollInterval);
        }
    }, 500);
}

function updateMissionStatus(data) {
    document.getElementById('mission-status-strip').style.display = 'block';
    const infoDiv = document.getElementById('mission-info');

    const statusClass = {
        completed: 'status-completed',
        error: 'status-error',
        running: 'status-running',
    }[data.status] || 'status-init';

    infoDiv.innerHTML = `
        <div class="status-grid">
            <div class="stat-tile">
                <div class="st-label">Status</div>
                <div class="st-value ${statusClass}" style="font-size:13px;">${data.status.toUpperCase()}</div>
            </div>
            <div class="stat-tile">
                <div class="st-label">Battery</div>
                <div class="st-value">${data.battery_level.toFixed(0)}</div>
                <div class="st-unit">%</div>
            </div>
            <div class="stat-tile">
                <div class="st-label">Samples</div>
                <div class="st-value">${data.samples_count}</div>
            </div>
        </div>
        <div class="progress-bar" style="margin-top:8px;">
            <div class="progress-fill" style="width: ${data.progress}%"></div>
        </div>
        <div class="progress-label">${data.progress.toFixed(0)}% — Location ${data.current_location} — [${data.rover_position[0].toFixed(1)}, ${data.rover_position[1].toFixed(1)}]</div>
    `;

    // Mirror to logs tab
    const infoLogs = document.getElementById('mission-info-logs');
    if (infoLogs) infoLogs.innerHTML = infoDiv.innerHTML;

    if (data.sensor_readings && Object.keys(data.sensor_readings).length > 0) {
        updateSensorDisplay(data.sensor_readings);
    }
    drawTerrainMap(data);
}

// Sensor thresholds for status dots — tuned for the LUNAR environment
// (South Pole-Aitken Basin: vacuum, ~0% humidity, -180°C surface, high cosmic dose)
const SENSOR_THRESHOLDS = {
    temperature:  { type: 'range',  normal: [-185, 130], warn: [-200, 140] }, // lunar surface range
    humidity:     { type: 'range',  normal: [0, 80],     warn: [0, 95] },      // ~0 nominal (no atmosphere)
    pressure:     { type: 'range',  normal: [0, 1100],   warn: [-1, 1200] },   // ~0 hPa vacuum nominal
    radiation:    { type: 'above',  warn: 90,   danger: 120 },                 // cosmic dose µSv/h
    pm25:         { type: 'above',  warn: 6,     danger: 12 },                  // regolith dust
    conductivity: { type: 'above',  warn: 0.5,   danger: 1.5 },                // dry regolith
    scattering:   { type: 'above',  warn: 0.05,  danger: 0.2 },
};

function getSensorLevel(key, val) {
    const t = SENSOR_THRESHOLDS[key];
    if (!t) return 'normal';
    if (t.type === 'above') {
        if (val >= t.danger) return 'danger';
        if (val >= t.warn)   return 'warn';
        return 'normal';
    }
    if (val < t.warn[0] || val > t.warn[1])     return 'danger';
    if (val < t.normal[0] || val > t.normal[1]) return 'warn';
    return 'normal';
}

// Map of data key → { element id, status id suffix, format function }
const SENSOR_MAP = {
    temperature:   { id: 'sv-temp',        sid: 'temp',         fmt: v => v.toFixed(1) },
    humidity:      { id: 'sv-humidity',     sid: 'humidity',     fmt: v => v.toFixed(1) },
    pressure:      { id: 'sv-pressure',     sid: 'pressure',     fmt: v => v.toFixed(0) },
    radiation:     { id: 'sv-radiation',    sid: 'radiation',    fmt: v => v.toFixed(1) },
    conductivity:  { id: 'sv-conductivity', sid: 'conductivity', fmt: v => v.toFixed(3) },
    pm25:          { id: 'sv-pm25',         sid: 'pm25',         fmt: v => v.toFixed(1) },
    abs_470nm:     { id: 'sv-abs470',       sid: 'abs470',       fmt: v => v.toFixed(4) },
    abs_850nm:     { id: 'sv-abs850',       sid: 'abs850',       fmt: v => v.toFixed(4) },
    scattering:    { id: 'sv-scatter',       sid: 'scatter',      fmt: v => v.toFixed(4) },
};

function updateSensorDisplay(readings) {
    Object.entries(SENSOR_MAP).forEach(([key, cfg]) => {
        const val = readings[key];
        if (val === undefined || val === null) return;
        const el = document.getElementById(cfg.id);
        if (!el) return;
        const newText = cfg.fmt(Number(val));
        if (el.textContent !== newText) {
            el.textContent = newText;
            const row = el.closest('.slp-row');
            if (row) { row.classList.remove('flash'); void row.offsetWidth; row.classList.add('flash'); }
        }
        // Status dot
        if (cfg.sid) {
            const level = getSensorLevel(key, Number(val));
            const sEl = document.getElementById(`slps-${cfg.sid}`);
            if (sEl) {
                sEl.className = `slp-status status-${level}`;
                sEl.textContent = level === 'normal' ? '✓' : level === 'warn' ? '!' : '⚠';
            }
        }
    });

    // GPS row
    if (readings.gps_lat !== undefined) {
        const gpsEl = document.getElementById('sv-gps');
        if (gpsEl) gpsEl.textContent = `${Number(readings.gps_lat).toFixed(6)}, ${Number(readings.gps_lon).toFixed(6)}`;
    }

    // Timestamp
    if (readings.timestamp) {
        const tsEl = document.getElementById('live-ts');
        if (tsEl) tsEl.textContent = readings.timestamp;
    }
}

// Terrain Map Visualization
// roverState may be a mission update (has rover_position) or controller state (has x,y)
function drawTerrainMap(roverState = null) {
    const canvas = document.getElementById('terrain-canvas');
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const CX = W / 2, CY = H / 2;
    const SCALE = 7;  // pixels per metre

    const worldToCanvas = (wx, wy) => [CX + wx * SCALE, CY - wy * SCALE];

    // Background
    ctx.fillStyle = '#eef2f7';
    ctx.fillRect(0, 0, W, H);

    // Grid lines
    ctx.strokeStyle = 'rgba(30,58,95,0.08)';
    ctx.lineWidth = 1;
    const gridStep = SCALE * 5;  // every 5 m
    for (let x = CX % gridStep; x < W; x += gridStep) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let y = CY % gridStep; y < H; y += gridStep) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }

    // Axis lines
    ctx.strokeStyle = 'rgba(30,58,95,0.18)';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(CX, 0); ctx.lineTo(CX, H); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, CY); ctx.lineTo(W, CY); ctx.stroke();

    // Hazard zones (from controller state)
    const zones = (_roverState && _roverState.hazard_zones) || [];
    const zoneColors = {
        radiation: { fill: 'rgba(220,38,38,.12)', stroke: '#dc2626', label: '#dc2626' },
        debris:    { fill: 'rgba(217,119,6,.12)',  stroke: '#d97706', label: '#b45309' },
        slope:     { fill: 'rgba(124,58,237,.12)', stroke: '#7c3aed', label: '#6d28d9' },
        crater:    { fill: 'rgba(75,85,99,.12)',   stroke: '#4b5563', label: '#374151' },
    };
    zones.forEach(zone => {
        const [zx, zy] = worldToCanvas(zone.x, zone.y);
        const r = zone.radius * SCALE;
        const c = zoneColors[zone.type] || zoneColors.debris;
        ctx.fillStyle = c.fill;
        ctx.strokeStyle = c.stroke;
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 3]);
        ctx.beginPath(); ctx.arc(zx, zy, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = c.label;
        ctx.font = 'bold 9px sans-serif'; ctx.textAlign = 'center';
        ctx.fillText(zone.label, zx, zy + r + 11);
    });

    // Sample sites
    const sites = (_roverState && _roverState.sample_sites) || [];
    const near = _roverState && _roverState.nearest_sample;
    sites.forEach(site => {
        const [sx, sy] = worldToCanvas(site.x, site.y);
        const isTarget = near && near.id === site.id;
        if (site.collected) {
            // Collected — faded checkmark
            ctx.fillStyle = 'rgba(22,163,74,.18)';
            ctx.beginPath(); ctx.arc(sx, sy, 7, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#16a34a';
            ctx.font = 'bold 11px sans-serif'; ctx.textAlign = 'center';
            ctx.fillText('✓', sx, sy + 4);
        } else {
            // Pending — diamond marker
            const size = isTarget ? 9 : 7;
            ctx.save();
            ctx.translate(sx, sy);
            ctx.rotate(Math.PI / 4);
            ctx.fillStyle = isTarget ? '#16a34a' : '#d97706';
            ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5;
            ctx.fillRect(-size, -size, size * 2, size * 2);
            ctx.strokeRect(-size, -size, size * 2, size * 2);
            ctx.restore();
            // Pulsing target ring
            if (isTarget && near.in_range) {
                ctx.strokeStyle = 'rgba(22,163,74,.6)'; ctx.lineWidth = 2;
                ctx.setLineDash([3, 3]);
                ctx.beginPath(); ctx.arc(sx, sy, 14, 0, Math.PI * 2); ctx.stroke();
                ctx.setLineDash([]);
            }
            // Label
            ctx.fillStyle = '#1e3a5f';
            ctx.font = 'bold 8px sans-serif'; ctx.textAlign = 'center';
            ctx.fillText(`${site.id} ${site.type}`, sx, sy - 11);
        }
    });

    // Collection-range ring around the rover
    if (_roverState && _roverState.x !== undefined) {
        const [rx0, ry0] = worldToCanvas(_roverState.x, _roverState.y);
        ctx.strokeStyle = 'rgba(217,119,6,.25)'; ctx.lineWidth = 1;
        ctx.setLineDash([2, 4]);
        ctx.beginPath(); ctx.arc(rx0, ry0, 3 * SCALE, 0, Math.PI * 2); ctx.stroke();
        ctx.setLineDash([]);
    }

    // Base / origin marker
    ctx.fillStyle = 'rgba(220,38,38,.2)';
    ctx.beginPath(); ctx.arc(CX, CY, 8, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#dc2626';
    ctx.font = 'bold 9px sans-serif'; ctx.textAlign = 'center';
    ctx.fillText('BASE', CX, CY + 19);

    // Controller rover trail
    const trail = (_roverState && _roverState.trail) || [];
    if (trail.length > 1) {
        ctx.strokeStyle = 'rgba(37,99,235,.35)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        trail.forEach(([tx, ty], i) => {
            const [cx2, cy2] = worldToCanvas(tx, ty);
            i === 0 ? ctx.moveTo(cx2, cy2) : ctx.lineTo(cx2, cy2);
        });
        ctx.stroke();
        ctx.setLineDash([]);
    }

    // Mission rover (from mission update)
    if (roverState && roverState.rover_position) {
        const [mx, my] = roverState.rover_position;
        const [sx, sy] = worldToCanvas(mx, my);
        ctx.fillStyle = 'rgba(39,174,96,.18)';
        ctx.beginPath(); ctx.arc(sx, sy, 10, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#16a34a';
        ctx.beginPath(); ctx.arc(sx, sy, 5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#1e3a5f';
        ctx.font = '9px monospace'; ctx.textAlign = 'left';
        ctx.fillText(`M [${mx.toFixed(1)}, ${my.toFixed(1)}]`, sx + 8, sy - 3);
    }

    // Controller rover (from manual controller state)
    if (_roverState && (_roverState.x !== undefined)) {
        const { x, y, heading } = _roverState;
        const [rx, ry] = worldToCanvas(x, y);
        const headRad = (heading - 90) * Math.PI / 180;   // convert to canvas angle (0°=up)

        // Glow
        const inDanger = (_roverState.alerts || []).some(a => a.severity === 'DANGER');
        ctx.fillStyle = inDanger ? 'rgba(220,38,38,.2)' : 'rgba(37,99,235,.18)';
        ctx.beginPath(); ctx.arc(rx, ry, 13, 0, Math.PI * 2); ctx.fill();

        // Body
        ctx.fillStyle = inDanger ? '#dc2626' : '#1d4ed8';
        ctx.beginPath(); ctx.arc(rx, ry, 6, 0, Math.PI * 2); ctx.fill();

        // Heading arrow
        const arrowLen = 16;
        const ax = rx + Math.cos(headRad) * arrowLen;
        const ay = ry + Math.sin(headRad) * arrowLen;
        ctx.strokeStyle = inDanger ? '#dc2626' : '#1d4ed8';
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(rx, ry); ctx.lineTo(ax, ay); ctx.stroke();
        // Arrowhead
        const tipAngle = Math.atan2(ay - ry, ax - rx);
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(ax - 6 * Math.cos(tipAngle - 0.4), ay - 6 * Math.sin(tipAngle - 0.4));
        ctx.lineTo(ax - 6 * Math.cos(tipAngle + 0.4), ay - 6 * Math.sin(tipAngle + 0.4));
        ctx.closePath(); ctx.fillStyle = inDanger ? '#dc2626' : '#1d4ed8'; ctx.fill();

        // Label
        ctx.fillStyle = '#1e3a5f';
        ctx.font = 'bold 9px monospace'; ctx.textAlign = 'left';
        ctx.fillText(`ROVER (${x.toFixed(1)}, ${y.toFixed(1)})`, rx + 14, ry - 4);
        ctx.font = '8px monospace';
        ctx.fillText(`hdg: ${heading.toFixed(0)}°`, rx + 14, ry + 7);
    }

    // Scale bar (bottom-left)
    ctx.strokeStyle = '#4a5568'; ctx.lineWidth = 1.5; ctx.setLineDash([]);
    const sb = 10 * SCALE;  // 10 m bar
    ctx.beginPath(); ctx.moveTo(10, H - 14); ctx.lineTo(10 + sb, H - 14); ctx.stroke();
    ctx.fillStyle = '#4a5568'; ctx.font = '8px sans-serif'; ctx.textAlign = 'left';
    ctx.fillText('10 m', 14, H - 5);
}

// Logging Functions
function addLog(message) {
    const timestamp = new Date().toLocaleTimeString();

    // Full log (Logs tab)
    const logsContainer = document.getElementById('logs-container');
    if (logsContainer) {
        if (logsContainer.querySelector('.placeholder')) logsContainer.innerHTML = '';
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.innerHTML = `<span class="log-time">${timestamp}</span>${message}`;
        logsContainer.appendChild(entry);
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }

    // Mini feed (dashboard)
    const mini = document.getElementById('mini-log-container');
    if (mini) {
        if (mini.querySelector('.placeholder')) mini.innerHTML = '';
        const e2 = document.createElement('div');
        e2.className = 'mini-log-entry';
        e2.innerHTML = `<span class="log-time">${timestamp}</span>${message}`;
        mini.appendChild(e2);
        while (mini.children.length > 5) mini.removeChild(mini.firstChild);
    }

    // Badge on logs tab when not viewing it
    const logsPane = document.getElementById('tab-logs');
    if (logsPane && !logsPane.classList.contains('active')) {
        _unreadLogs++;
        const btn = document.querySelector('[data-tab="logs"]');
        if (btn) btn.innerHTML = `Mission Logs <span class="tab-badge">${_unreadLogs}</span>`;
    }
}

// Sample Display
async function updateSamplesList() {
    if (!activeMissionId) return;

    try {
        const response = await fetch(`${API_BASE}/api/missions/${activeMissionId}/status`);
        const data = await response.json();

        const samplesContainer = document.getElementById('samples-container');
        const samples = data.samples || [];

        if (samples.length === 0) {
            samplesContainer.innerHTML = '<p class="placeholder">No samples collected yet</p>';
            return;
        }

        let samplesHTML = '';
        samples.forEach(sample => {
            samplesHTML += `
                <div class="sample-item">
                    <div class="sample-id">${sample.id}</div>
                    <div class="sample-type">Type: ${sample.type}</div>
                    <div class="sample-confidence">Confidence: ${(sample.confidence * 100).toFixed(0)}%</div>
                </div>
            `;
        });

        samplesContainer.innerHTML = samplesHTML;
    } catch (error) {
        console.error('Error updating samples list:', error);
    }
}

// Report Functions
async function viewReport() {
    if (!activeMissionId) return;

    try {
        const response = await fetch(`${API_BASE}/api/missions/${activeMissionId}/report`);
        const report = await response.json();

        displayReport(report);
        document.getElementById('report-modal').style.display = 'flex';
    } catch (error) {
        console.error('Error fetching report:', error);
        alert('Error loading report: ' + error.message);
    }
}

function displayReport(report) {
    const reportContent = document.getElementById('report-content');

    let html = `
        <div class="report-section">
            <h3>Mission Summary</h3>
            <div class="report-stats">
                <div class="stat-box">
                    <div class="stat-value">${report.samples_collected}</div>
                    <div class="stat-label">Samples Collected</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">${report.battery_remaining.toFixed(1)}%</div>
                    <div class="stat-label">Battery Remaining</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">${report.locations_explored}</div>
                    <div class="stat-label">Locations Explored</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">${Math.round(report.duration_seconds)}s</div>
                    <div class="stat-label">Duration</div>
                </div>
            </div>
        </div>

        <div class="report-section">
            <h3>Final Sensor Readings</h3>
            <div class="report-stats">
                <div class="stat-box">
                    <div class="stat-value">${report.final_sensor_readings.temperature?.toFixed(1) || '--'}°C</div>
                    <div class="stat-label">Temperature</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">${report.final_sensor_readings.humidity?.toFixed(1) || '--'}%</div>
                    <div class="stat-label">Humidity</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">${report.final_sensor_readings.radiation?.toFixed(3) || '--'}</div>
                    <div class="stat-label">Radiation (mSv/h)</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">${report.final_sensor_readings.conductivity?.toFixed(2) || '--'}</div>
                    <div class="stat-label">Conductivity (mS/cm)</div>
                </div>
            </div>
        </div>

        <div class="report-section">
            <h3>Top Samples by Scientific Value</h3>
            <table class="sample-table">
                <thead>
                    <tr>
                        <th>Sample ID</th>
                        <th>Type</th>
                        <th>Confidence</th>
                        <th>Location</th>
                    </tr>
                </thead>
                <tbody>
    `;

    report.top_samples.forEach(sample => {
        html += `
            <tr>
                <td>${sample.id}</td>
                <td>${sample.type.toUpperCase()}</td>
                <td>${(sample.confidence * 100).toFixed(0)}%</td>
                <td>${sample.location || '--'}</td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>
        </div>

        <div class="report-section">
            <h3>Mission Log</h3>
            <div class="logs" style="max-height: 200px;">
    `;

    report.log_entries.forEach(entry => {
        const time = new Date(entry.timestamp).toLocaleTimeString();
        html += `<div class="log-entry"><span class="log-time">${time}</span>${entry.message}</div>`;
    });

    html += `
            </div>
        </div>
    `;

    reportContent.innerHTML = html;
}

function closeReportModal() {
    document.getElementById('report-modal').style.display = 'none';
}

// Active Missions List
async function updateActiveMissionsList() {
    try {
        const response = await fetch(`${API_BASE}/api/missions/active`);
        const missions = await response.json();

        const missionsList = document.getElementById('missions-list');

        if (missions.length === 0) {
            missionsList.innerHTML = '<p class="placeholder">No active missions</p>';
            return;
        }

        let html = '';
        missions.forEach(mission => {
            const isActive = mission.mission_id === activeMissionId;
            html += `
                <div class="mission-item ${isActive ? 'active' : ''}" onclick="selectMission('${mission.mission_id}')">
                    <div class="mission-item-title">${mission.mission_type}</div>
                    <div class="mission-item-status">${mission.status.toUpperCase()} - ${mission.progress.toFixed(0)}%</div>
                    <div class="mission-item-status">Samples: ${mission.samples_found}</div>
                </div>
            `;
        });

        missionsList.innerHTML = html;
    } catch (error) {
        console.error('Error updating missions list:', error);
    }
}

function selectMission(missionId) {
    activeMissionId = missionId;
    updateActiveMissionsList();
    pollMissionStatus(missionId);
}

// Connection Status
function updateConnectionStatus(connected) {
    const el = document.getElementById('connection-status');
    el.textContent = connected ? '● Connected' : '● Disconnected';
    el.className = connected ? 'conn-status connected' : 'conn-status disconnected';
}

// Sensor Testing Functions
let selectedTest = null;

async function handleSensorChange(event) {
    const sensorType = event.target.value;
    const capabilitiesDiv = document.getElementById('sensor-capabilities');
    const runBtn = document.getElementById('run-test-btn');

    if (!sensorType) {
        capabilitiesDiv.innerHTML = '<p class="placeholder">Select a sensor to see capabilities</p>';
        runBtn.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/sensors/${sensorType}/capabilities`);
        const data = await response.json();
        const tests = data.available_tests || [];

        if (tests.length === 0) {
            capabilitiesDiv.innerHTML = '<p class="placeholder">No tests available for this sensor</p>';
            runBtn.style.display = 'none';
            selectedTest = null;
            return;
        }

        const html = tests.map((test, idx) => `
            <div class="capability-item${idx === 0 ? ' selected' : ''}"
                 data-sensor="${sensorType}" data-type="${test.type}" data-name="${test.name.replace(/"/g, '&quot;')}">
                <span class="capability-name">${test.name}</span>
                <span class="capability-desc">${test.description}</span>
            </div>
        `).join('');

        capabilitiesDiv.innerHTML = html;

        // Wire clicks (avoids quoting issues with inline onclick)
        capabilitiesDiv.querySelectorAll('.capability-item').forEach(el => {
            el.addEventListener('click', () => selectTest(el));
        });

        // Auto-select the first test so "Run" works immediately
        selectedTest = { sensor: sensorType, type: tests[0].type, name: tests[0].name };
        runBtn.style.display = 'block';
        runBtn.disabled = false;
        runBtn.textContent = 'Run Selected Test';
    } catch (error) {
        console.error('Error loading sensor capabilities:', error);
        capabilitiesDiv.innerHTML = '<p class="placeholder">Error loading capabilities</p>';
    }
}

function selectTest(element) {
    document.querySelectorAll('.capability-item').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');
    selectedTest = {
        sensor: element.dataset.sensor,
        type: element.dataset.type,
        name: element.dataset.name,
    };
}

async function runSensorTest() {
    if (!selectedTest) {
        alert('Please select a test to run');
        return;
    }

    const btn = document.getElementById('run-test-btn');
    btn.disabled = true;
    btn.textContent = 'Running...';

    try {
        addLog(`🔬 Starting sensor test: ${selectedTest.name}`);

        const response = await fetch(`${API_BASE}/api/sensors/${selectedTest.sensor}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ analysis_type: selectedTest.type })
        });

        const result = await response.json();

        if (result.error) {
            addLog(`❌ Test failed: ${result.error}`);
            return;
        }

        // Display results
        const analysis = result.analysis;
        addLog(`✅ ${analysis.analysis}: ${analysis.result}`);

        // Show detailed results in a formatted way
        displayTestResults(selectedTest.sensor, analysis);

    } catch (error) {
        console.error('Error running test:', error);
        addLog(`❌ Error: ${error.message}`);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Run Selected Test';
    }
}

function displayTestResults(sensor, analysis) {
    const panel = document.getElementById('sensor-results-body');
    if (!panel) return;

    const fmtVal = (value) => {
        if (value === null || value === undefined) return '—';
        if (typeof value === 'number') return Number.isInteger(value) ? value : value.toFixed(3);
        if (typeof value === 'object') {
            // Render small objects as key:val pairs
            return Object.entries(value)
                .map(([k, v]) => `${formatKey(k)}: ${typeof v === 'number' ? (Number.isInteger(v) ? v : v.toFixed(2)) : v}`)
                .join(', ');
        }
        return value;
    };

    const headline = analysis.result || analysis.analysis || 'Result';
    let html = `
        <div class="result-headline">
            <div class="result-title">${analysis.analysis || formatKey(sensor)}</div>
            <div class="result-summary">${headline}</div>
        </div>
        <div class="result-grid">`;

    Object.entries(analysis).forEach(([key, value]) => {
        if (key === 'analysis' || key === 'result') return;
        html += `
            <div class="result-pair">
                <span class="result-key">${formatKey(key)}</span>
                <span class="result-val">${fmtVal(value)}</span>
            </div>`;
    });
    html += '</div>';

    panel.innerHTML = html;
}

function formatKey(key) {
    return key
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .trim()
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Polling for active missions
setInterval(updateActiveMissionsList, 2000);
setInterval(updateSamplesList, 1000);

// ── Rover Controller ──────────────────────────────────────────────────────────

let _roverState = { x: 0, y: 0, heading: 0, battery: 100, odometer: 0, trail: [], hazard_zones: [] };
let _ctrlHeld = new Set();

async function moveRover(direction) {
    const btnMap = { forward: 'btn-fwd', back: 'btn-back', left: 'btn-left', right: 'btn-right' };
    const btn = btnMap[direction] ? document.getElementById(btnMap[direction]) : null;
    if (btn) { btn.classList.add('pressed'); setTimeout(() => btn.classList.remove('pressed'), 180); }

    try {
        const res = await fetch(`${API_BASE}/api/rover/move`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ direction, steps: 1 })
        });
        const data = await res.json();
        if (!data.error) applyRoverState(data);
    } catch (e) { console.error('Rover move error', e); }
}

async function rotateRover(degrees) {
    try {
        const res = await fetch(`${API_BASE}/api/rover/rotate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ degrees })
        });
        const data = await res.json();
        if (!data.error) applyRoverState(data);
    } catch (e) { console.error('Rotate error', e); }
}

async function setSpeed(val) {
    document.getElementById('speed-label').textContent = `${val} m`;
    await fetch(`${API_BASE}/api/rover/speed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speed: parseFloat(val) })
    });
}

function applyRoverState(state) {
    _roverState = state;

    // Stats bar
    document.getElementById('ctrl-batt').textContent = `🔋 ${state.battery.toFixed(0)}%`;
    document.getElementById('ctrl-odo').textContent  = `📏 ${state.odometer.toFixed(1)} m`;
    const coordStr = `x: ${state.x.toFixed(1)}, y: ${state.y.toFixed(1)} | hdg: ${state.heading.toFixed(0)}°`;
    ['rover-coords', 'rover-coords-map'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = coordStr;
    });

    // Hazard strip
    const strip = document.getElementById('hazard-strip');
    const alerts = state.alerts || [];
    if (alerts.length === 0) {
        strip.innerHTML = '';
    } else {
        strip.innerHTML = alerts.map(a =>
            `<span class="hazard-tag ${a.severity}">${a.severity === 'DANGER' ? '⚠' : '!'} ${a.label}${a.distance_m !== undefined ? ' (' + a.distance_m + ' m)' : ''}</span>`
        ).join('');
    }

    // Nearest-sample readout + collect button
    updateCollectUI(state.nearest_sample);

    // Field scanner (direction + probability)
    updateFieldScanner(state.field_scan);

    // Redraw map
    drawTerrainMap(state);
}

// Arrow glyph per compass point
const COMPASS_ARROWS = { N:'↑', NE:'↗', E:'→', SE:'↘', S:'↓', SW:'↙', W:'←', NW:'↖' };
let _scanNotified = { samples: false, debris: false, radiation: false };

function updateFieldScanner(scan) {
    if (!scan) return;
    ['samples', 'debris', 'radiation'].forEach(cat => {
        const d = scan[cat];
        const arrowEl = document.getElementById(`scan-${cat}-arrow`);
        const fillEl  = document.getElementById(`scan-${cat}-fill`);
        const pctEl   = document.getElementById(`scan-${cat}-pct`);
        const row     = document.querySelector(`.scan-row[data-cat="${cat}"]`);
        if (!arrowEl || !fillEl || !pctEl) return;

        if (!d) {
            arrowEl.textContent = '✓';
            fillEl.style.width = '0%';
            pctEl.textContent = '—';
            if (row) row.classList.remove('hot');
            return;
        }

        const pct = Math.round(d.probability * 100);
        arrowEl.textContent = d.arrow || COMPASS_ARROWS[d.compass] || '·';
        arrowEl.title = `${d.compass} · nearest ${d.nearest_m} m`;
        fillEl.style.width = `${pct}%`;
        pctEl.textContent = `${pct}%`;

        const hot = d.probability >= 0.6;
        if (row) row.classList.toggle('hot', hot);

        // Notify once when a category becomes high-probability
        if (hot && !_scanNotified[cat]) {
            _scanNotified[cat] = true;
            const labels = { samples: '🪨 Sample-rich zone', debris: '⛰ Debris field', radiation: '☢ Radiation source' };
            addLog(`${labels[cat]} likely ${pct}% — bearing ${d.compass} (${d.nearest_m} m)`);
        } else if (!hot) {
            _scanNotified[cat] = false;
        }
    });
}

function updateCollectUI(near) {
    const btn = document.getElementById('collect-btn');
    const label = document.getElementById('nearest-sample');
    if (!btn || !label) return;

    if (!near) {
        btn.disabled = true;
        btn.classList.remove('ready');
        label.textContent = '✓ All samples collected';
        label.classList.remove('in-range');
        return;
    }
    if (near.in_range) {
        btn.disabled = false;
        btn.classList.add('ready');
        label.textContent = `${near.id} ${near.type} — in range (${near.distance} m)`;
        label.classList.add('in-range');
    } else {
        btn.disabled = true;
        btn.classList.remove('ready');
        label.textContent = `Nearest: ${near.id} ${near.type} — ${near.distance} m away`;
        label.classList.remove('in-range');
    }
}

async function collectSample() {
    try {
        const res = await fetch(`${API_BASE}/api/rover/collect`, { method: 'POST' });
        const data = await res.json();
        addLog(data.ok ? `🪨 ${data.message}` : `⚠ ${data.message}`);
        if (data.x !== undefined) applyRoverState(data);
        if (data.ok) renderCollectedSamples(data.collected_samples);
    } catch (e) { console.error('Collect error', e); }
}

function renderCollectedSamples(samples) {
    if (!samples) return;
    const html = samples.length === 0
        ? '<p class="placeholder">No samples yet</p>'
        : samples.map(s => `
            <div class="sample-item">
                <div class="sample-id">${s.id} · ${s.type}</div>
                <div class="sample-confidence">Scientific value: ${(s.value * 100).toFixed(0)}%</div>
            </div>`).join('');
    ['samples-container', 'samples-container-logs'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = html;
    });
}

// Keyboard controls: WASD + diagonals + Q/E rotate
const KEY_MOVE_MAP = {
    ArrowUp: 'forward',    w: 'forward',  W: 'forward',
    ArrowDown: 'back',     s: 'back',     S: 'back',
    ArrowLeft: 'left',     a: 'left',     A: 'left',
    ArrowRight: 'right',   d: 'right',    D: 'right',
};
const SCROLL_KEYS = new Set(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' ']);

document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
    if (SCROLL_KEYS.has(e.key)) e.preventDefault();

    // Rotation
    if ((e.key === 'q' || e.key === 'Q') && !_ctrlHeld.has('q')) {
        _ctrlHeld.add('q'); rotateRover(-45); return;
    }
    if ((e.key === 'e' || e.key === 'E') && !_ctrlHeld.has('e')) {
        _ctrlHeld.add('e'); rotateRover(45); return;
    }
    // Collect sample
    if ((e.key === 'c' || e.key === 'C') && !_ctrlHeld.has('c')) {
        _ctrlHeld.add('c'); collectSample(); return;
    }

    const dir = KEY_MOVE_MAP[e.key];
    if (dir && !_ctrlHeld.has(dir)) {
        _ctrlHeld.add(dir);
        moveRover(dir);
    }
});
document.addEventListener('keyup', (e) => {
    _ctrlHeld.delete(KEY_MOVE_MAP[e.key]);
    if (e.key === 'q' || e.key === 'Q') _ctrlHeld.delete('q');
    if (e.key === 'e' || e.key === 'E') _ctrlHeld.delete('e');
    if (e.key === 'c' || e.key === 'C') _ctrlHeld.delete('c');
});

// Fetch initial rover state on load
(async function() {
    try {
        const res = await fetch(`${API_BASE}/api/rover/state`);
        const data = await res.json();
        applyRoverState(data);
    } catch(e) {}
})();
