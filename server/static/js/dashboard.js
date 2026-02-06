const CAMERA_ORDER = ['front', 'rear', 'left', 'right'];
const KEY_BINDINGS = { KeyW: 'FORWARD', KeyA: 'LEFT', KeyS: 'BACKWARD', KeyD: 'RIGHT', Space: 'STOP' };

const mockState = {
  items: [
    {
      id: 'rover-01',
      mode: 'AUTO',
      pdd_state: 'ON_TRACK',
      gps: { lat: 55.7512, lon: 37.6184 },
      route: [[55.7512, 37.6184], [55.7521, 37.6196], [55.753, 37.6211]],
      goal: { lat: 55.753, lon: 37.6211 },
      streams: { front: 'Front', rear: 'Rear', left: 'Left', right: 'Right' },
    },
  ],
};

let selectedRover = null;
let fetchEnabled = !window.location.protocol.startsWith('file');
let map;
let roverMarker;
let routeLine;
let goalMarker;

function setSubtitle(text) {
  document.getElementById('subtitle').textContent = text;
}

async function apiFetch(path, options = {}) {
  if (!fetchEnabled) return null;

  try {
    const response = await fetch(path, options);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (_) {
    fetchEnabled = false;
    setSubtitle('API недоступен. Demo-режим включён.');
    return null;
  }
}

function ensureLocalAssetsFallback() {
  if (window.location.protocol !== 'file:') return;

  document.querySelectorAll('link[href^="../static/"]').forEach((item) => {
    item.href = item.href.replace('../static/', './static/');
  });
  document.querySelectorAll('script[src^="../static/"]').forEach((item) => {
    item.src = item.src.replace('../static/', './static/');
  });
}

function getMockRovers() {
  return { items: mockState.items.map(({ id, mode, pdd_state, gps }) => ({ id, mode, pdd_state, gps })) };
}

function getMockStatus(roverId) {
  return mockState.items.find((rover) => rover.id === roverId) || {};
}

function addMockRover(roverId) {
  const exists = mockState.items.some((item) => item.id === roverId);
  if (exists) return;
  mockState.items.push({
    id: roverId,
    mode: 'MANUAL',
    pdd_state: 'STOP',
    gps: { lat: 55.75, lon: 37.61 },
    route: [],
    goal: null,
    streams: { front: 'Front', rear: 'Rear', left: 'Left', right: 'Right' },
  });
}

function renderRovers(data) {
  const list = document.getElementById('rover-list');
  list.innerHTML = '';

  data.items.forEach((rover) => {
    const li = document.createElement('li');
    li.className = `rover-item ${rover.id === selectedRover ? 'active' : ''}`;
    li.innerHTML = `<strong>${rover.id}</strong><div class="rover-meta">${rover.mode || '--'} · ${rover.pdd_state || '--'}</div>`;
    li.addEventListener('click', () => {
      selectedRover = rover.id;
      loadDashboard();
    });
    list.appendChild(li);
  });

  if (!selectedRover && data.items.length) {
    selectedRover = data.items[0].id;
  }
}

function renderCameras(streams = {}) {
  const grid = document.getElementById('camera-grid');
  grid.innerHTML = '';

  CAMERA_ORDER.forEach((camera) => {
    const item = document.createElement('article');
    item.className = 'camera-box';
    item.innerHTML = `<b>${camera.toUpperCase()}</b><div>${streams[camera] || 'Stream unavailable'}</div>`;
    grid.appendChild(item);
  });
}

function initMap() {
  if (typeof L === 'undefined') {
    document.getElementById('route-status').textContent = 'Leaflet недоступен в этом режиме.';
    return;
  }

  map = L.map('map').setView([55.7512, 37.6184], 14);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map);

  roverMarker = L.circleMarker([55.7512, 37.6184], {
    radius: 7,
    color: '#62a8ff',
    fillColor: '#62a8ff',
    fillOpacity: 1,
  }).addTo(map);

  routeLine = L.polyline([], { color: '#7f9eff', weight: 4 }).addTo(map);

  map.on('click', async (event) => {
    if (!selectedRover) return;
    const goal = { lat: event.latlng.lat, lon: event.latlng.lng };
    await sendGoal(goal);
  });
}

function updateMap(status) {
  const gps = status.gps || {};
  const lat = Number(gps.lat);
  const lon = Number(gps.lon);
  const goal = status.goal || null;

  document.getElementById('route-status').textContent =
    `GPS: ${Number.isFinite(lat) ? lat.toFixed(6) : '--'}, ${Number.isFinite(lon) ? lon.toFixed(6) : '--'} | ` +
    `Статус: ${status.pdd_state || '--'} | ` +
    `Цель: ${goal ? `${goal.lat.toFixed(6)}, ${goal.lon.toFixed(6)}` : '--'}`;

  if (!map || !Number.isFinite(lat) || !Number.isFinite(lon)) return;

  roverMarker.setLatLng([lat, lon]);
  routeLine.setLatLngs(Array.isArray(status.route) ? status.route : []);

  if (goal && Number.isFinite(goal.lat) && Number.isFinite(goal.lon)) {
    if (!goalMarker) {
      goalMarker = L.marker([goal.lat, goal.lon]).addTo(map);
    } else {
      goalMarker.setLatLng([goal.lat, goal.lon]);
    }
  }

  map.panTo([lat, lon], { animate: true, duration: 0.5 });
}

function renderStatus(status) {
  document.getElementById('rover-title').textContent = status.id || selectedRover || 'Rover';
  document.getElementById('mode-pill').textContent = `MODE: ${status.mode || '--'}`;
  const pdd = document.getElementById('pdd-pill');
  pdd.textContent = `PDD: ${status.pdd_state || '--'}`;
  pdd.classList.toggle('pill-stop', status.pdd_state === 'STOP');

  renderCameras(status.streams || {});
  updateMap(status);
}

async function sendCommand(type, payload = {}) {
  if (!selectedRover) return;

  if (!fetchEnabled) {
    setSubtitle(`Demo: ${type} для ${selectedRover}`);
    return;
  }

  await apiFetch(`/rovers/${selectedRover}/command`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type, payload }),
  });
}

async function sendGoal(goal) {
  if (!selectedRover) return;

  if (!fetchEnabled) {
    const rover = mockState.items.find((item) => item.id === selectedRover);
    if (rover) rover.goal = goal;
    setSubtitle(`Demo: цель ${goal.lat.toFixed(5)}, ${goal.lon.toFixed(5)} отправлена`);
    await loadDashboard();
    return;
  }

  await apiFetch(`/rovers/${selectedRover}/goal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(goal),
  });
  setSubtitle(`Цель отправлена: ${goal.lat.toFixed(5)}, ${goal.lon.toFixed(5)}`);
}

async function createRover(roverId) {
  if (!roverId) return;

  if (!fetchEnabled) {
    addMockRover(roverId);
    selectedRover = roverId;
    setSubtitle(`Demo: создан ${roverId}`);
    await loadDashboard();
    return;
  }

  const response = await apiFetch('/rovers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: roverId }),
  });

  if (response?.ok) {
    selectedRover = roverId;
    setSubtitle(`Ровер ${roverId} добавлен`);
    await loadDashboard();
  }
}

async function loadDashboard() {
  const rovers = (await apiFetch('/rovers')) || getMockRovers();
  renderRovers(rovers);

  if (!selectedRover) {
    setSubtitle('Нет активных роверов');
    return;
  }

  const status = (await apiFetch(`/rovers/${selectedRover}/status`)) || getMockStatus(selectedRover);
  renderStatus(status || {});
  if (fetchEnabled) setSubtitle('Синхронизация с REST API активна');
}

function bindControls() {
  document.querySelectorAll('[data-cmd]').forEach((button) => {
    button.addEventListener('click', async () => {
      const command = button.dataset.cmd;
      if (command === 'STOP') await sendCommand('stop');
      else await sendCommand('drive', { command, speed: 35 });
    });
  });

  document.getElementById('auto-btn').addEventListener('click', () => sendCommand('set_mode', { mode: 'AUTO' }));
  document.getElementById('manual-btn').addEventListener('click', () => sendCommand('set_mode', { mode: 'MANUAL' }));

  window.addEventListener('keydown', async (event) => {
    const command = KEY_BINDINGS[event.code];
    if (!command) return;
    event.preventDefault();

    if (command === 'STOP') await sendCommand('stop');
    else await sendCommand('drive', { command, speed: 35 });
  });

  document.getElementById('add-rover-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const input = document.getElementById('new-rover-id');
    const roverId = input.value.trim();
    if (!roverId) return;
    await createRover(roverId);
    input.value = '';
  });
}

ensureLocalAssetsFallback();
initMap();
bindControls();
loadDashboard();
setInterval(loadDashboard, 1500);
