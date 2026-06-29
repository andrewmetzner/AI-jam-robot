// Rover Mission Control Web App
const API_BASE = 'http://localhost:5000';
let socket;
let activeMissionId = null;
let missionData = {};
let moonMapData = null;
let astronautSafetySnapshot = null;
let recentAlerts = [];
let missionTrail = [];

// ── Moon terrain image (revealed by fog-of-war as the rover explores) ──────────
const MOON_IMG = new Image();
let moonImgLoaded = false;
MOON_IMG.onload = () => { moonImgLoaded = true; drawTerrainMap(); };
MOON_IMG.src = '/static/MoonDEM.png';

// Camera / zoom config for the lunar map
const MAP_PXPM = 11;        // pixels per metre (higher = more zoomed in)
const MAP_VISION_M = 9;     // field-of-vision reveal radius in metres
const MOON_SPAN_X = 170;    // metres the moon image spans horizontally (tiled)
const MOON_SPAN_Y = 85;     // metres vertically

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Rover Mission Control Web App');

    initializeWebSocket();
    setupEventListeners();
    loadMoonMap();
    fetchAstronautHealth();
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
        loadMoonMap();
        fetchAstronautHealth();
        fetchRecentAlerts();
    });

    socket.on('live_sensor', (data) => {
        updateSensorDisplay(data);
    });

    socket.on('safety_snapshot', (data) => {
        astronautSafetySnapshot = data;
        updateAstronautHealth(data);
    });

    socket.on('safety_alert', (alert) => {
        if (!alert) return;
        prependSafetyAlert(alert);
        const severity = (alert.severity || 'normal').toUpperCase();
        const title = alert.title || 'Safety alert';
        addLog(`${severity}: ${title} - ${alert.message || ''}`.trim());
    });

    socket.on('safety_alerts', (alerts) => {
        renderSafetyAlerts(alerts || []);
    });

    socket.on('rover_moved', (data) => {
        applyRoverState(data);
    });

    socket.on('simulation_reset', (data) => {
        plannedPath = [];
        missionTrail = [];
        autoDriving = false;
        activeMissionId = null;
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
        missionTrail = [];

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
    if (Array.isArray(data.rover_position) && data.rover_position.length >= 2) {
        const [mx, my] = data.rover_position;
        const last = missionTrail[missionTrail.length - 1];
        if (!last || last[0] !== mx || last[1] !== my) {
            missionTrail.push([mx, my]);
            if (missionTrail.length > 200) {
                missionTrail = missionTrail.slice(-200);
            }
        }
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
    const SCALE = MAP_PXPM;  // pixels per metre

    // Camera follows the active rover. A running mission takes priority so the
    // mission rover stays centered; otherwise follow the manual WASD controller.
    let camX = 0, camY = 0;
    if (roverState && roverState.rover_position) { camX = roverState.rover_position[0]; camY = roverState.rover_position[1]; }
    else if (_roverState && _roverState.x !== undefined) { camX = _roverState.x; camY = _roverState.y; }

    const worldToCanvas = (wx, wy) => [CX + (wx - camX) * SCALE, CY - (wy - camY) * SCALE];

    // Deep-space backdrop (unexplored void)
    ctx.fillStyle = '#05070d';
    ctx.fillRect(0, 0, W, H);

    // Moon terrain image, tiled in world space (this is what fog reveals)
    drawMoonBase(ctx, worldToCanvas, SCALE, camX, camY, W, H);

    // Subtle grid over terrain for scale reference
    ctx.strokeStyle = 'rgba(120,140,170,0.10)';
    ctx.lineWidth = 1;
    const gridStep = SCALE * 5;  // every 5 m
    const [ox] = worldToCanvas(0, 0);
    for (let x = ((ox % gridStep) + gridStep) % gridStep; x < W; x += gridStep) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    const [, oy] = worldToCanvas(0, 0);
    for (let y = ((oy % gridStep) + gridStep) % gridStep; y < H; y += gridStep) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }

    // NOTE: hazard zones, sample sites and the collection ring are drawn in the
    // foreground pass (renderMapFeatures) AFTER the fog, so they stay visible
    // above the moon image and the fog overlay.

    // Base / origin marker (landing site at world origin)
    const [bx, by] = worldToCanvas(0, 0);
    ctx.fillStyle = 'rgba(220,38,38,.25)';
    ctx.beginPath(); ctx.arc(bx, by, 8, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#dc2626';
    ctx.font = 'bold 9px sans-serif'; ctx.textAlign = 'center';
    ctx.fillText('BASE', bx, by + 19);

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

    // Fog mask first, then all markers ABOVE it so samples / debris / radiation
    // circles are always visible over the moon image and the fog.
    renderFogOfWar(ctx, worldToCanvas, SCALE, roverState);
    renderMapFeatures(ctx, worldToCanvas, SCALE);
    renderRoverForeground(ctx, worldToCanvas, SCALE, roverState);

    if (moonMapData) {
        updateMoonMapSummary(moonMapData);
    }
}

// Hazard zones, sample sites and the collection ring — drawn above the fog so
// they always appear over the moon terrain.
function renderMapFeatures(ctx, worldToCanvas, SCALE) {
    // Planned safe route (drawn first so markers sit on top)
    if (plannedPath && plannedPath.length > 1) {
        ctx.save();
        // glow underlay
        ctx.strokeStyle = 'rgba(45,212,191,.35)';
        ctx.lineWidth = 6; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
        ctx.beginPath();
        plannedPath.forEach(([wx, wy], i) => {
            const [cx, cy] = worldToCanvas(wx, wy);
            i === 0 ? ctx.moveTo(cx, cy) : ctx.lineTo(cx, cy);
        });
        ctx.stroke();
        // dashed core line
        ctx.strokeStyle = '#14b8a6';
        ctx.lineWidth = 2; ctx.setLineDash([6, 4]);
        ctx.beginPath();
        plannedPath.forEach(([wx, wy], i) => {
            const [cx, cy] = worldToCanvas(wx, wy);
            i === 0 ? ctx.moveTo(cx, cy) : ctx.lineTo(cx, cy);
        });
        ctx.stroke();
        ctx.setLineDash([]);
        // waypoint dots + goal flag
        plannedPath.forEach(([wx, wy], i) => {
            const [cx, cy] = worldToCanvas(wx, wy);
            if (i === plannedPath.length - 1) {
                ctx.fillStyle = '#14b8a6';
                ctx.font = 'bold 13px sans-serif'; ctx.textAlign = 'center';
                ctx.fillText('⚑', cx, cy - 8);
            } else if (i > 0) {
                ctx.fillStyle = 'rgba(20,184,166,.9)';
                ctx.beginPath(); ctx.arc(cx, cy, 2.5, 0, Math.PI * 2); ctx.fill();
            }
        });
        ctx.restore();
    }
    // Hazard zones (radiation / debris / slope / crater)
    const zones = (_roverState && _roverState.hazard_zones) || [];
    const zoneColors = {
        radiation: { fill: 'rgba(220,38,38,.22)', stroke: '#f87171', label: '#fca5a5' },
        debris:    { fill: 'rgba(217,119,6,.22)',  stroke: '#fbbf24', label: '#fcd34d' },
        slope:     { fill: 'rgba(124,58,237,.22)', stroke: '#a78bfa', label: '#c4b5fd' },
        crater:    { fill: 'rgba(148,163,184,.22)', stroke: '#cbd5e1', label: '#e2e8f0' },
    };
    zones.forEach(zone => {
        const [zx, zy] = worldToCanvas(zone.x, zone.y);
        const r = zone.radius * SCALE;
        const c = zoneColors[zone.type] || zoneColors.debris;
        ctx.fillStyle = c.fill;
        ctx.strokeStyle = c.stroke;
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 3]);
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
            ctx.fillStyle = 'rgba(22,163,74,.30)';
            ctx.beginPath(); ctx.arc(sx, sy, 7, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#4ade80';
            ctx.font = 'bold 11px sans-serif'; ctx.textAlign = 'center';
            ctx.fillText('✓', sx, sy + 4);
        } else {
            const size = isTarget ? 9 : 7;
            ctx.save();
            ctx.translate(sx, sy);
            ctx.rotate(Math.PI / 4);
            ctx.fillStyle = isTarget ? '#22c55e' : '#f59e0b';
            ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5;
            ctx.fillRect(-size, -size, size * 2, size * 2);
            ctx.strokeRect(-size, -size, size * 2, size * 2);
            ctx.restore();
            if (isTarget && near.in_range) {
                ctx.strokeStyle = 'rgba(74,222,128,.8)'; ctx.lineWidth = 2;
                ctx.setLineDash([3, 3]);
                ctx.beginPath(); ctx.arc(sx, sy, 14, 0, Math.PI * 2); ctx.stroke();
                ctx.setLineDash([]);
            }
            // Label with dark halo so it reads over bright terrain
            ctx.font = 'bold 8px sans-serif'; ctx.textAlign = 'center';
            ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(4,6,12,.8)';
            ctx.strokeText(`${site.id} ${site.type}`, sx, sy - 11);
            ctx.fillStyle = '#fde68a';
            ctx.fillText(`${site.id} ${site.type}`, sx, sy - 11);
        }
    });

    // Collection-range ring around the rover
    if (_roverState && _roverState.x !== undefined) {
        const [rx0, ry0] = worldToCanvas(_roverState.x, _roverState.y);
        ctx.strokeStyle = 'rgba(245,158,11,.5)'; ctx.lineWidth = 1.2;
        ctx.setLineDash([2, 4]);
        ctx.beginPath(); ctx.arc(rx0, ry0, 3 * SCALE, 0, Math.PI * 2); ctx.stroke();
        ctx.setLineDash([]);
    }
}

// Draw the moon terrain image tiled across world space (only matters where fog is lifted)
function drawMoonBase(ctx, worldToCanvas, pxpm, camX, camY, W, H) {
    if (!moonImgLoaded) {
        ctx.fillStyle = '#0c1018';
        ctx.fillRect(0, 0, W, H);
        return;
    }
    // World bounds currently visible
    const halfW = (W / 2) / pxpm, halfH = (H / 2) / pxpm;
    const minX = camX - halfW, maxX = camX + halfW;
    const minY = camY - halfH, maxY = camY + halfH;

    // Which image tiles cover the view (tile i centered at i*SPAN)
    const iMin = Math.floor((minX + MOON_SPAN_X / 2) / MOON_SPAN_X);
    const iMax = Math.floor((maxX + MOON_SPAN_X / 2) / MOON_SPAN_X);
    const jMin = Math.floor((minY + MOON_SPAN_Y / 2) / MOON_SPAN_Y);
    const jMax = Math.floor((maxY + MOON_SPAN_Y / 2) / MOON_SPAN_Y);

    const destW = MOON_SPAN_X * pxpm;
    const destH = MOON_SPAN_Y * pxpm;
    ctx.imageSmoothingEnabled = true;
    for (let i = iMin; i <= iMax; i++) {
        for (let j = jMin; j <= jMax; j++) {
            const cx = i * MOON_SPAN_X, cy = j * MOON_SPAN_Y;       // tile centre in world
            // top-left world corner of this tile
            const [dx, dy] = worldToCanvas(cx - MOON_SPAN_X / 2, cy + MOON_SPAN_Y / 2);
            // Mirror alternate tiles so seams are less obvious
            ctx.save();
            ctx.translate(dx, dy);
            if ((i + j) & 1) { ctx.translate(destW, 0); ctx.scale(-1, 1); }
            ctx.drawImage(MOON_IMG, 0, 0, destW, destH);
            ctx.restore();
        }
    }
    // Cool lunar tint
    ctx.save();
    ctx.globalCompositeOperation = 'multiply';
    ctx.fillStyle = 'rgba(150,160,185,0.85)';
    ctx.fillRect(0, 0, W, H);
    ctx.restore();
}

function getExploredPoints(roverState = null) {
    const points = [];
    let prev = null;
    const addPoint = (point) => {
        if (!Array.isArray(point) || point.length < 2) return;
        const x = Number(point[0]);
        const y = Number(point[1]);
        if (!Number.isFinite(x) || !Number.isFinite(y)) return;
        // Interpolate from the previous point so big jumps (mission waypoints
        // ~25 m apart) reveal as a continuous corridor instead of dotted holes.
        if (prev) {
            const dx = x - prev[0], dy = y - prev[1];
            const dist = Math.hypot(dx, dy);
            const steps = Math.floor(dist / 4);   // a reveal point every ~4 m
            for (let i = 1; i < steps; i++) {
                points.push([prev[0] + (dx * i) / steps, prev[1] + (dy * i) / steps]);
            }
        }
        const last = points[points.length - 1];
        if (!last || Math.abs(last[0] - x) > 0.05 || Math.abs(last[1] - y) > 0.05) {
            points.push([x, y]);
        }
        prev = [x, y];
    };

    // Landing site is known from the start; everything else must be driven near.
    addPoint([0, 0]);
    prev = null;
    ((_roverState && _roverState.trail) || []).forEach(addPoint);
    if (_roverState && _roverState.x !== undefined) addPoint([_roverState.x, _roverState.y]);
    prev = null;
    missionTrail.forEach(addPoint);
    if (roverState && roverState.rover_position) addPoint(roverState.rover_position);
    return points;
}

function renderFogOfWar(ctx, worldToCanvas, scale, roverState = null) {
    const canvas = ctx.canvas;
    const revealRadius = MAP_VISION_M * scale;
    const points = getExploredPoints(roverState);

    // Opaque lunar-night fog; punch soft holes where the rover has had line of sight
    ctx.save();
    ctx.fillStyle = 'rgba(4, 6, 12, 0.97)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.globalCompositeOperation = 'destination-out';

    points.forEach(([wx, wy]) => {
        const [cx, cy] = worldToCanvas(wx, wy);
        const gradient = ctx.createRadialGradient(cx, cy, revealRadius * 0.45, cx, cy, revealRadius);
        gradient.addColorStop(0, 'rgba(0,0,0,1)');
        gradient.addColorStop(0.7, 'rgba(0,0,0,.9)');
        gradient.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(cx, cy, revealRadius, 0, Math.PI * 2);
        ctx.fill();
    });
    ctx.restore();

    // Bright vision ring around the rover's current field of view
    if (_roverState && _roverState.x !== undefined) {
        const [cx, cy] = worldToCanvas(_roverState.x, _roverState.y);
        ctx.save();
        ctx.strokeStyle = 'rgba(120,190,255,0.22)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.beginPath(); ctx.arc(cx, cy, revealRadius, 0, Math.PI * 2); ctx.stroke();
        ctx.restore();
    }

    // Explored percentage readout
    ctx.save();
    ctx.fillStyle = 'rgba(200,215,240,0.6)';
    ctx.font = 'bold 9px monospace';
    ctx.textAlign = 'right';
    ctx.fillText(`EXPLORED ${Math.min(99, Math.round(points.length * 1.2))}%`, canvas.width - 12, canvas.height - 10);
    ctx.restore();
}

function renderRoverForeground(ctx, worldToCanvas, scale, roverState = null) {
    const canvas = ctx.canvas;

    const drawTrail = (trail, color) => {
        if (!Array.isArray(trail) || trail.length < 2) return;
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.7;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        trail.forEach(([tx, ty], i) => {
            const [cx, cy] = worldToCanvas(tx, ty);
            i === 0 ? ctx.moveTo(cx, cy) : ctx.lineTo(cx, cy);
        });
        ctx.stroke();
        ctx.setLineDash([]);
    };

    drawTrail((_roverState && _roverState.trail) || [], 'rgba(147,197,253,.9)');
    drawTrail(missionTrail, 'rgba(74,222,128,.85)');

    if (roverState && roverState.rover_position) {
        const [mx, my] = roverState.rover_position;
        const [sx, sy] = worldToCanvas(mx, my);
        ctx.fillStyle = 'rgba(74,222,128,.25)';
        ctx.beginPath(); ctx.arc(sx, sy, 12, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#22c55e';
        ctx.beginPath(); ctx.arc(sx, sy, 5, 0, Math.PI * 2); ctx.fill();
    }

    if (_roverState && _roverState.x !== undefined) {
        const { x, y, heading } = _roverState;
        const [rx, ry] = worldToCanvas(x, y);
        const headRad = (heading - 90) * Math.PI / 180;
        const inDanger = (_roverState.alerts || []).some(a => a.severity === 'DANGER');
        const roverColor = inDanger ? '#dc2626' : '#38bdf8';

        ctx.fillStyle = inDanger ? 'rgba(220,38,38,.24)' : 'rgba(56,189,248,.25)';
        ctx.beginPath(); ctx.arc(rx, ry, 14, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = roverColor;
        ctx.beginPath(); ctx.arc(rx, ry, 6, 0, Math.PI * 2); ctx.fill();

        const ax = rx + Math.cos(headRad) * 17;
        const ay = ry + Math.sin(headRad) * 17;
        ctx.strokeStyle = roverColor;
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(rx, ry); ctx.lineTo(ax, ay); ctx.stroke();
    }

    ctx.strokeStyle = 'rgba(255,255,255,.7)';
    ctx.lineWidth = 1.5;
    const sb = 10 * scale;
    ctx.beginPath(); ctx.moveTo(10, canvas.height - 14); ctx.lineTo(10 + sb, canvas.height - 14); ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,.75)';
    ctx.font = '8px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('10 m', 14, canvas.height - 5);
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

async function fetchAstronautHealth() {
    try {
        const res = await fetch(`${API_BASE}/api/astronaut/health`);
        if (!res.ok) return;
        const data = await res.json();
        astronautSafetySnapshot = data;
        updateAstronautHealth(data);
    } catch (e) {
        // server not ready yet â€” will catch up on next push
    }
}

async function fetchRecentAlerts() {
    try {
        const res = await fetch(`${API_BASE}/api/alerts`);
        if (!res.ok) return;
        const data = await res.json();
        renderSafetyAlerts(data || []);
    } catch (e) {
        // ignore until the websocket snapshot arrives
    }
}

async function loadMoonMap() {
    try {
        const res = await fetch(`${API_BASE}/api/lunar-map?rows=10&cols=16`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.error) return;
        moonMapData = data;
        updateMoonMapSummary(data);
        drawTerrainMap();
    } catch (e) {
        // ignore during server warm-up
    }
}

function updateAstronautHealth(snapshot) {
    const hrEl = document.getElementById('astronaut-hr');
    const statusEl = document.getElementById('astronaut-hr-status');
    const radEl = document.getElementById('astronaut-radiation');
    const pressureEl = document.getElementById('astronaut-pressure');
    const warningList = document.getElementById('astronaut-warning-signs');

    if (!snapshot) return;

    const prediction = snapshot.prediction || {};
    const conditions = snapshot.conditions || {};
    const hr = prediction.predicted_heart_rate ?? snapshot.biometrics?.heart_rate;
    const status = (prediction.heart_rate_status || snapshot.health_status || 'nominal').toLowerCase();
    const statusLabel = status.toUpperCase();
    const statusText = snapshot.recommendation?.action
        ? `${statusLabel} - ${snapshot.recommendation.action.replace(/_/g, ' ')}`
        : statusLabel;

    if (hrEl && hr !== undefined) hrEl.textContent = hr;
    if (statusEl) {
        statusEl.textContent = statusText;
        statusEl.className = `health-status-pill status-${status}`;
    }
    if (radEl) radEl.textContent = Number(conditions.radiation_usv_h ?? 0).toFixed(1);
    if (pressureEl) pressureEl.textContent = Number(conditions.suit_pressure ?? 0).toFixed(1);

    if (warningList) {
        const warnings = [];
        if (snapshot.radiation_alert) warnings.push(snapshot.radiation_alert.message);
        if (Array.isArray(prediction.warning_signs)) warnings.push(...prediction.warning_signs);
        if (Array.isArray(snapshot.health_alerts)) warnings.push(...snapshot.health_alerts);
        if (Array.isArray(snapshot.suit_alerts)) warnings.push(...snapshot.suit_alerts);

        const uniqueWarnings = [...new Set(warnings.filter(Boolean))];
        if (uniqueWarnings.length === 0) {
            warningList.innerHTML = '<li>No active warning signs</li>';
        } else {
            warningList.innerHTML = uniqueWarnings.map(w => `<li>${escapeHtml(w)}</li>`).join('');
        }
    }
}

function renderSafetyAlerts(alerts) {
    const container = document.getElementById('alerts-container');
    if (!container) return;

    recentAlerts = Array.isArray(alerts) ? alerts.slice() : [];
    if (recentAlerts.length === 0) {
        container.innerHTML = '<p class="placeholder">No active alerts</p>';
        return;
    }

    container.innerHTML = recentAlerts.slice(0, 8).map(renderSafetyAlert).join('');
}

function prependSafetyAlert(alert) {
    if (!alert) return;
    const signature = `${alert.category || 'general'}:${alert.severity || 'normal'}:${alert.message || ''}`;
    const filtered = recentAlerts.filter(a => `${a.category || 'general'}:${a.severity || 'normal'}:${a.message || ''}` !== signature);
    recentAlerts = [alert, ...filtered].slice(0, 8);
    renderSafetyAlerts(recentAlerts);
}

function renderSafetyAlert(alert) {
    const severity = (alert.severity || 'normal').toLowerCase();
    const title = alert.title || 'Safety alert';
    const message = alert.message || '';
    const recommendation = alert.recommendation || '';
    return `
        <div class="alert-item alert-${severity}">
            <div class="alert-top">
                <span class="alert-title">${escapeHtml(title)}</span>
                <span class="alert-badge">${severity.toUpperCase()}</span>
            </div>
            <div class="alert-message">${escapeHtml(message)}</div>
            ${recommendation ? `<div class="alert-recommendation">${escapeHtml(recommendation)}</div>` : ''}
        </div>
    `;
}

function updateMoonMapSummary(data) {
    const el = document.getElementById('moon-map-summary');
    if (!el) return;
    if (!data || !data.summary) {
        el.textContent = 'Lunar probability surface unavailable.';
        return;
    }

    const s = data.summary;
    const source = data.source || {};
    const best = s.best_cell || {};
    const richest = s.richest_cell || {};
    const riskiest = s.riskiest_cell || {};
    const iciest = s.iciest_cell || {};
    const agri = s.agri_cell || {};

    el.innerHTML = `
        <div class="moon-summary-row">
            <strong>Best zone</strong>
            <span>${Math.round((best.composite_probability || 0) * 100)}%</span>
            <span>${best.label || 'Survey Zone'}</span>
        </div>
        <div class="moon-summary-row">
            <strong>Richest resource</strong>
            <span>${Math.round((richest.resource_probability || 0) * 100)}%</span>
            <span>${richest.label || 'sample potential'}</span>
        </div>
        <div class="moon-summary-row">
            <strong>Ice deposit</strong>
            <span>${Math.round((iciest.ice_probability || 0) * 100)}%</span>
            <span>row ${iciest.row ?? '--'}, col ${iciest.col ?? '--'}</span>
        </div>
        <div class="moon-summary-row">
            <strong>Agri-viable</strong>
            <span>${Math.round((agri.agriculture_score || 0) * 100)}%</span>
            <span>${agri.label || 'soil'}</span>
        </div>
        <div class="moon-summary-row">
            <strong>Highest hazard</strong>
            <span>${Math.round((riskiest.hazard_probability || 0) * 100)}%</span>
            <span>${riskiest.label || 'Radiation Watch'}</span>
        </div>
        <div class="moon-summary-note">${escapeHtml(source.note || 'Modeled from the lunar datasets in the workspace.')} ${source.resource_survey_points ? `(${source.resource_survey_points} resource survey points)` : ''}</div>
    `;
}

function renderMoonProbabilityLayer(ctx, worldToCanvas, scale) {
    if (!moonMapData || !moonMapData.cells) return;

    const rows = moonMapData.summary?.rows || 10;
    const cols = moonMapData.summary?.cols || 16;
    const worldWidth = 48;
    const worldHeight = 34;
    const cellWidth = worldWidth / cols;
    const cellHeight = worldHeight / rows;

    moonMapData.cells.forEach(cell => {
        const centerX = cell.x_norm * (worldWidth / 2);
        const centerY = cell.y_norm * (worldHeight / 2);
        const [cx, cy] = worldToCanvas(centerX, centerY);
        const width = cellWidth * scale;
        const height = cellHeight * scale;

        let color;
        if ((cell.hazard_probability || 0) >= 0.75) {
            color = `rgba(220, 38, 38, ${0.12 + (cell.hazard_probability || 0) * 0.38})`;
        } else if ((cell.resource_probability || 0) >= 0.70) {
            color = `rgba(245, 158, 11, ${0.12 + (cell.resource_probability || 0) * 0.36})`;
        } else {
            color = `rgba(59, 130, 246, ${0.08 + (cell.safe_probability || 0) * 0.28})`;
        }

        ctx.fillStyle = color;
        ctx.fillRect(cx - width / 2, cy - height / 2, width, height);
    });
}

function escapeHtml(text) {
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
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

// ── Full simulation restart ───────────────────────────────────────────────────
async function restartSimulation() {
    if (!confirm('Restart the whole simulation? This clears the route, samples, missions and explored map.')) return;

    // Stop any local activity
    autoDriving = false;
    plannedPath = [];
    missionTrail = [];
    activeMissionId = null;

    try {
        const res = await fetch(`${API_BASE}/api/simulation/reset`, { method: 'POST' });
        const data = await res.json();

        // Wipe frontend panels back to their initial state
        const reset = (id, html) => { const el = document.getElementById(id); if (el) el.innerHTML = html; };
        reset('logs-container', '<p class="placeholder">Logs appear here during a mission</p>');
        reset('samples-container', '<p class="placeholder">No samples yet</p>');
        reset('samples-container-logs', '<p class="placeholder">No samples yet</p>');
        reset('mission-info', '<p class="placeholder">No active mission</p>');
        reset('mission-info-logs', '<p class="placeholder">No active mission</p>');
        const strip = document.getElementById('mission-status-strip');
        if (strip) strip.style.display = 'none';
        const pathInfo = document.getElementById('path-info');
        if (pathInfo) { pathInfo.textContent = ''; pathInfo.classList.remove('danger'); }
        const adBtn = document.getElementById('autodrive-btn');
        if (adBtn) adBtn.disabled = true;
        const reportBtn = document.getElementById('view-report-btn');
        if (reportBtn) reportBtn.style.display = 'none';

        applyRoverState(data);
        addLog('⟳ Simulation restarted — back to the landing site.');
    } catch (e) {
        console.error('Restart error', e);
        alert('Could not restart simulation: ' + e.message);
    }
}

// ── Hazard-aware path planning ────────────────────────────────────────────────
let plannedPath = [];
let autoDriving = false;

async function planSafePath() {
    const info = document.getElementById('path-info');
    info.classList.remove('danger');
    info.textContent = 'Planning safe route…';
    try {
        const res = await fetch(`${API_BASE}/api/rover/plan_path`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})   // default = nearest uncollected sample
        });
        const data = await res.json();
        if (!data.ok) {
            plannedPath = [];
            info.classList.add('danger');
            info.textContent = data.message || 'No safe route found.';
            document.getElementById('autodrive-btn').disabled = true;
            drawTerrainMap();
            return;
        }
        plannedPath = data.waypoints || [];
        const exposureTxt = data.hazard_exposure > 25 ? ' ⚠ some exposure' : ' ✓ low exposure';
        info.textContent = `→ ${data.goal}: ${data.length_m} m,${exposureTxt}`;
        document.getElementById('autodrive-btn').disabled = false;
        addLog(`🛰 ${data.message}`);
        drawTerrainMap();
    } catch (e) {
        info.classList.add('danger');
        info.textContent = 'Route planning failed.';
        console.error('plan path error', e);
    }
}

async function toggleAutoDrive() {
    const btn = document.getElementById('autodrive-btn');
    if (autoDriving) { autoDriving = false; return; }     // stop request
    if (!plannedPath.length) return;

    autoDriving = true;
    btn.classList.add('running');
    btn.textContent = '■ Stop';

    // Drive through waypoints, skipping the first (current position)
    for (let i = 1; i < plannedPath.length; i++) {
        if (!autoDriving) break;
        const [x, y] = plannedPath[i];
        try {
            const res = await fetch(`${API_BASE}/api/rover/goto`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ x, y })
            });
            const data = await res.json();
            if (!data.error) applyRoverState(data);
        } catch (e) { console.error('auto-drive step error', e); break; }
        await new Promise(r => setTimeout(r, 320));        // animation pacing
    }

    autoDriving = false;
    btn.classList.remove('running');
    btn.textContent = '▶ Auto-Drive';

    // Arrived — try to collect if a sample is in range
    if (_roverState && _roverState.nearest_sample && _roverState.nearest_sample.in_range) {
        collectSample();
    }
    addLog('🛰 Auto-drive complete.');
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
        if (data.ok) {
            // Route consumed — clear the planned path and its UI
            plannedPath = [];
            document.getElementById('autodrive-btn').disabled = true;
            const info = document.getElementById('path-info');
            if (info) { info.textContent = ''; info.classList.remove('danger'); }
            renderCollectedSamples(data.collected_samples);
        }
        if (data.x !== undefined) applyRoverState(data);
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
