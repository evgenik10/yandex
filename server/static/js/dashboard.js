const CAMERA_ORDER = ['front', 'rear', 'left', 'right'];
const KEY_BINDINGS = { KeyW: 'FORWARD', KeyA: 'LEFT', KeyS: 'BACKWARD', KeyD: 'RIGHT', Space: 'STOP' };

const mockState = {
  items: [
    {
      id: 'rover-01',
      mode: 'AUTO',
      pdd_state: 'ON_TRACK',
      gps: { lat: 55.7512, lon: 37.6184 },
      route: [
        [55.7512, 37.6184],
        [55.7525, 37.6201],
        [55.7532, 37.6216],
      ],
      streams: {
        front: 'Front stream',
        rear: 'Rear stream',
        left: 'Left stream',
        right: 'Right stream',
      },
    },
    {
      id: 'rover-02',
      mode: 'MANUAL',
      pdd_state: 'RETURNING',
      gps: { lat: 55.7461, lon: 37.6054 },
      route: [
        [55.7461, 37.6054],
        [55.7472, 37.607],
      ],
      streams: {
        front: 'Front stream',
        rear: 'Rear stream',
        left: 'Left stream',
        right: 'Right stream',
      },
    },
  ],
};

let selectedRover = null;
let fetchEnabled = !window.location.protocol.startsWith('file');
let map;
let roverMarker;
let routeLine;

async function apiFetch(path, options = {}) {
  if (!fetchEnabled) {
    return null;
  }

  try {
    const response = await fetch(path, options);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.json();
  } catch (_) {
    fetchEnabled = false;
    setSubtitle('API недоступен, включён demo-режим');
    return null;
  }
}

function setSubtitle(text) {
  document.getElementById('rover-subtitle').textContent = text;
}

function getMockRovers() {
  return { items: mockState.items.map(({ id, mode, pdd_state }) => ({ id, mode, pdd_state })) };
}

function getMockStatus(roverId) {
  return mockState.items.find((rover) => rover.id === roverId) || mockState.items[0];
}

function initMap() {
  if (typeof L === 'undefined') {
    document.getElementById('route-status').textContent = 'Карта недоступна офлайн (Leaflet не загружен)';
    return;
  }

  map = L.map('map', { zoomControl: true }).setView([55.7512, 37.6184], 14);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map);

  roverMarker = L.circleMarker([55.7512, 37.6184], {
    radius: 8,
    color: '#57a6ff',
    fillColor: '#57a6ff',
    fillOpacity: 0.9,
  }).addTo(map);

  routeLine = L.polyline([], { color: '#7f8cff', weight: 4 }).addTo(map);
}

function renderRoverList(data) {
  const list = document.getElementById('rover-list');
  list.innerHTML = '';

  data.items.forEach((rover) => {
    const li = document.createElement('li');
    li.className = rover.id === selectedRover ? 'active' : '';
    li.innerHTML = `<strong>${rover.id}</strong><div class="muted">${rover.mode || '--'} · ${rover.pdd_state || '--'}</div>`;
    li.onclick = () => {
      selectedRover = rover.id;
      loadDashboard();
    };
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
    const card = document.createElement('article');
    card.className = 'camera-card';
    card.innerHTML = `
      <div class="camera-title">${camera.toUpperCase()}</div>
      <div class="camera-content">${streams[camera] || 'stream unavailable'}</div>
    `;
    grid.appendChild(card);
  });
}

function updateMap(status) {
  const gps = status.gps || {};
  const lat = Number(gps.lat);
  const lon = Number(gps.lon);

  document.getElementById('route-status').textContent =
    `GPS: ${Number.isFinite(lat) ? lat.toFixed(6) : '--'}, ${Number.isFinite(lon) ? lon.toFixed(6) : '--'} | ` +
    `Маршрут: ${status.pdd_state || '--'}`;

  if (!map || !Number.isFinite(lat) || !Number.isFinite(lon)) {
    return;
  }

  const route = Array.isArray(status.route) ? status.route : [];
  roverMarker.setLatLng([lat, lon]);
  routeLine.setLatLngs(route);
  map.panTo([lat, lon], { animate: true, duration: 0.5 });
}

function renderStatus(status) {
  document.getElementById('rover-title').textContent = status.id || selectedRover || 'Rover';
  document.getElementById('mode-pill').textContent = `MODE: ${status.mode || '--'}`;

  const pdd = document.getElementById('pdd-pill');
  pdd.textContent = `PDD: ${status.pdd_state || '--'}`;
  pdd.classList.toggle('pdd-stop', status.pdd_state === 'STOP');

  renderCameras(status.streams || {});
  updateMap(status);
}

async function sendCommand(type, payload = {}) {
  if (!selectedRover) {
    return;
  }

  if (!fetchEnabled) {
    setSubtitle(`Demo: команда ${type} отправлена в mock`);
    return;
  }

  await apiFetch(`/rovers/${selectedRover}/command`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type, payload }),
  });
}

async function loadDashboard() {
  const rovers = (await apiFetch('/rovers')) || getMockRovers();
  renderRoverList(rovers);

  if (!selectedRover) {
    setSubtitle('Нет доступных роверов');
    return;
  }

  const status = (await apiFetch(`/rovers/${selectedRover}/status`)) || getMockStatus(selectedRover);
  renderStatus(status);
  setSubtitle(fetchEnabled ? 'Данные обновляются через REST API' : 'Demo-режим (без API)');
}

function bindControls() {
  document.querySelectorAll('[data-cmd]').forEach((button) => {
    button.addEventListener('click', async () => {
      const command = button.dataset.cmd;
      if (command === 'STOP') {
        await sendCommand('stop');
      } else {
        await sendCommand('drive', { command, speed: 35 });
      }
    });
  });

  document.getElementById('auto-btn').addEventListener('click', () => sendCommand('set_mode', { mode: 'AUTO' }));
  document.getElementById('manual-btn').addEventListener('click', () => sendCommand('set_mode', { mode: 'MANUAL' }));

  window.addEventListener('keydown', async (event) => {
    const command = KEY_BINDINGS[event.code];
    if (!command) {
      return;
    }
    event.preventDefault();

    if (command === 'STOP') {
      await sendCommand('stop');
      return;
    }

    await sendCommand('drive', { command, speed: 35 });
  });
}

initMap();
bindControls();
loadDashboard();
setInterval(loadDashboard, 1500);
