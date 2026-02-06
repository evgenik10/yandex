let selectedRover = null;

async function fetchJSON(url, options = {}) {
  const response = await fetch(url, options);
  return response.json();
}

async function loadRovers() {
  const data = await fetchJSON('/rovers');
  const list = document.getElementById('rover-list');
  list.innerHTML = '';

  data.items.forEach((rover) => {
    const li = document.createElement('li');
    li.textContent = `${rover.id} · ${rover.pdd_state}`;
    li.className = rover.id === selectedRover ? 'active' : '';
    li.onclick = () => {
      selectedRover = rover.id;
      renderStatus();
      loadRovers();
    };
    list.appendChild(li);
  });

  if (!selectedRover && data.items.length) {
    selectedRover = data.items[0].id;
    renderStatus();
    loadRovers();
  }
}

async function renderStatus() {
  if (!selectedRover) return;
  const status = await fetchJSON(`/rovers/${selectedRover}/status`);

  document.getElementById('rover-title').textContent = selectedRover;
  document.getElementById('mode-pill').textContent = `MODE: ${status.mode || '--'}`;
  const pdd = document.getElementById('pdd-pill');
  pdd.textContent = `PDD: ${status.pdd_state || '--'}`;
  pdd.className = status.pdd_state === 'STOP' ? 'pdd-stop' : '';

  const grid = document.getElementById('camera-grid');
  grid.innerHTML = '';
  const streams = status.streams || {};
  ['front', 'rear', 'left', 'right'].forEach((camera) => {
    const box = document.createElement('article');
    box.className = 'camera';
    box.innerHTML = `<h3>${camera.toUpperCase()}</h3><div class="stream">${streams[camera] || 'stream unavailable'}</div>`;
    grid.appendChild(box);
  });

  const gps = status.gps || {};
  document.getElementById('map-box').textContent =
    `GPS: ${gps.lat || '--'}, ${gps.lon || '--'} | ` +
    `PDD: ${status.pdd_state || '--'} | ` +
    `Объекты: ${(status.detections || []).length}`;
}

async function sendCommand(type, payload = {}) {
  if (!selectedRover) return;
  await fetchJSON(`/rovers/${selectedRover}/command`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type, payload }),
  });
}

document.querySelectorAll('[data-cmd]').forEach((button) => {
  button.onclick = async () => {
    const command = button.dataset.cmd;
    if (command === 'STOP') {
      await sendCommand('stop');
    } else {
      await sendCommand('drive', { command, speed: 35 });
    }
  };
});

document.getElementById('auto-btn').onclick = () => sendCommand('set_mode', { mode: 'AUTO' });
document.getElementById('manual-btn').onclick = () => sendCommand('set_mode', { mode: 'MANUAL' });

window.addEventListener('keydown', async (e) => {
  const map = { KeyW: 'FORWARD', KeyS: 'BACKWARD', KeyA: 'LEFT', KeyD: 'RIGHT', Space: 'STOP' };
  if (!map[e.code]) return;
  e.preventDefault();
  if (map[e.code] === 'STOP') await sendCommand('stop');
  else await sendCommand('drive', { command: map[e.code], speed: 35 });
});

setInterval(() => {
  loadRovers();
  renderStatus();
}, 1200);

loadRovers();
