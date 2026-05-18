const API_BASE = 'http://localhost:9000/api';

// --- Global State ---
let currentSlots = [];
let selectedSlotId = null;

// --- Shared Functions ---

async function fetchSlots() {
  try {
    const res = await fetch(`${API_BASE}/slots`);
    const data = await res.json();
    currentSlots = data.slots;
    return data; // { timestamp, slots: [] }
  } catch (e) {
    console.error("Fetch slots error:", e);
    return { slots: [] };
  }
}

async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/admin/stats`);
    return await res.json();
  } catch (e) {
    console.error("Fetch stats error:", e);
    return null;
  }
}

// --- User Portal Logic ---

function initUserPortal() {
  renderUserSlots();
  // Poll every 1s
  setInterval(renderUserSlots, 1000);
}

async function renderUserSlots() {
  const data = await fetchSlots();
  const container = document.getElementById('slot-container');

  // Update count
  const freeCount = data.slots.filter(s => s.status === 'FREE').length;
  const countEl = document.getElementById('free-count');
  if (countEl) countEl.innerText = freeCount;

  container.innerHTML = '';

  data.slots.forEach(slot => {
    const el = document.createElement('div');
    el.className = `parking-slot ${slot.status.toLowerCase()}`;

    let icon = '';
    let label = 'Available';

    if (slot.status === 'OCCUPIED') {
      icon = '<i class="fa-solid fa-car-side status-icon" style="font-size: 2rem; margin-bottom: 0.5rem"></i>';
      label = 'Occupied';
    } else if (slot.status === 'RESERVED') {
      icon = '<i class="fa-solid fa-clock status-icon" style="font-size: 2rem; margin-bottom: 0.5rem; color: var(--status-reserved)"></i>';
      label = 'Reserved';
    } else {
      icon = '<i class="fa-solid fa-square-parking status-icon" style="font-size: 2rem; margin-bottom: 0.5rem; color: var(--status-free)"></i>';
    }

    el.innerHTML = `
            <div class="slot-id">#${slot.id}</div>
            ${icon}
            <div class="status-text">${label}</div>
        `;

    // Interaction
    if (slot.status === 'FREE') {
      el.onclick = () => openModal(slot.id);
    }

    container.appendChild(el);
  });
}

// Modal Logic
function openModal(slotId) {
  selectedSlotId = slotId;
  document.getElementById('modal-slot-id').innerText = '#' + slotId;
  document.getElementById('reserve-modal').classList.add('active');
  document.getElementById('res-name').value = '';
  document.getElementById('res-plate').value = '';
}

function closeModal() {
  document.getElementById('reserve-modal').classList.remove('active');
  selectedSlotId = null;
}

async function confirmReservation() {
  const name = document.getElementById('res-name').value;
  const plate = document.getElementById('res-plate').value;

  if (!name || !plate) {
    alert("Please enter all details");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/reserve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slot_id: selectedSlotId, name, plate })
    });
    const json = await res.json();

    if (json.success) {
      closeModal();
      renderUserSlots(); // Refresh immediately
    } else {
      alert("Error: " + json.error);
    }
  } catch (e) {
    alert("Network error");
  }
}


// --- Admin Portal Logic ---

function initAdminPortal() {
  refreshAdmin();
  setInterval(refreshAdmin, 2000);
}

async function refreshAdmin() {
  // 1. Map (Mini)
  const data = await fetchSlots();
  const mapContainer = document.getElementById('slot-container');
  if (mapContainer) {
    mapContainer.innerHTML = '';
    data.slots.forEach(slot => {
      const el = document.createElement('div');
      el.className = `parking-slot ${slot.status.toLowerCase()}`;
      el.style.aspectRatio = "1"; // Squarer for admin
      el.innerHTML = `<div style="font-weight:bold">${slot.id}</div>`;
      mapContainer.appendChild(el);
    });
  }

  // 2. Stats
  const stats = await fetchStats();
  if (stats) {
    document.getElementById('stat-total').innerText = stats.total;
    document.getElementById('stat-available').innerText = stats.available;
    document.getElementById('stat-occupied').innerText = stats.occupied;
    document.getElementById('stat-reserved').innerText = stats.reserved;
  }

  // 3. Table
  const tbody = document.getElementById('reservations-table');
  const msg = document.getElementById('no-res-msg');

  // Filter slots that have reservations
  const reservedSlots = data.slots.filter(s => s.reservation);

  if (reservedSlots.length === 0) {
    tbody.innerHTML = '';
    msg.style.display = 'block';
  } else {
    msg.style.display = 'none';

    // Build rows
    // Using a simple check to avoid clearing input if we were editing (not applicable here, but good practice is diffing)
    // For now, full overwrite
    tbody.innerHTML = reservedSlots.map(slot => {
      const r = slot.reservation;
      const timeStr = new Date(r.reserved_at * 1000).toLocaleTimeString();

      // If the slot is physically occupied, warn admin
      const liveStatus = slot.raw_status === "OCCUPIED"
        ? '<span style="color:var(--status-occupied)"><i class="fa-solid fa-triangle-exclamation"></i> Driver Arrived</span>'
        : '<span style="color:var(--text-secondary)">Waiting...</span>';

      return `
                <tr>
                    <td><span style="font-weight:bold; color:var(--accent-primary)">#${slot.id}</span></td>
                    <td>${r.name}</td>
                    <td>${r.plate}</td>
                    <td>${timeStr}</td>
                    <td>${liveStatus}</td>
                    <td>
                        <button class="btn btn-danger" style="padding: 0.5rem 1rem; font-size: 0.8rem;" onclick="cancelReservation(${slot.id})">
                             Cancel
                        </button>
                    </td>
                </tr>
            `;
    }).join('');
  }
}

async function cancelReservation(slotId) {
  if (!confirm("Are you sure you want to cancel this reservation?")) return;

  try {
    const res = await fetch(`${API_BASE}/cancel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slot_id: slotId })
    });
    const json = await res.json();
    if (json.success) {
      refreshAdmin();
    } else {
      alert(json.error);
    }
  } catch (e) {
    alert("Network error");
  }
}
