// DSIS v3 — frontend logic. Talks to Python exclusively through
// `window.pywebview.api` (see python/gui_web/api.py). No mock/sample data
// lives here — every table, stat, and status pill is populated from a real
// backend call.

const PAGE_TITLES = {
  dashboard: 'Dashboard', attendance: 'Attendance', students: 'Students',
  reports: 'Reports', logs: 'Logs', settings: 'Settings',
};

let connected = false;
let scanning = false;
let selectedStudent = null;
let currentRole = 'admin';
let deviceFingerprintCount = null;
let connectionPollTimer = null;

function escapeHtml(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ── pywebview readiness ──
// pywebview injects window.pywebview only after the native window has
// finished bootstrapping, which can happen after our script runs.
function whenApiReady(fn) {
  if (window.pywebview && window.pywebview.api) { fn(); return; }
  window.addEventListener('pywebviewready', fn, { once: true });
}
function api() {
  return window.pywebview && window.pywebview.api;
}

// Called by Python (api.py -> Api._push) to stream live events into the UI.
window.dsisEvent = function (event, payload) {
  if (event === 'scan_result') handleScanResult(payload);
  else if (event === 'serial_line') smAppend(payload.text, payload.direction === 'tx' ? 'serial-tx' : 'serial-rx');
  else if (event === 'log_line') appendLiveLogLine(payload.line);
  else if (event === 'enroll_progress') handleEnrollProgress(payload);
  else if (event === 'delete_progress') handleDeleteProgress(payload);
  else if (event === 'wipe_progress') handleWipeProgress(payload);
  else if (event === 'fingerprint_count') handleFingerprintCount(payload);
  else if (event === 'connection_status') handleConnectionStatus(payload);
  else if (event === 'mode_changed') handleModeChanged(payload);
};

// ── Navigation ──
function nav(el, key) {
  document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
  el.classList.add('active');
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-' + key).classList.add('active');
  document.getElementById('page-title').textContent = PAGE_TITLES[key];

  if (key === 'dashboard') loadDashboard();
  else if (key === 'attendance') loadAttendancePage();
  else if (key === 'students') loadStudentsPage();
  else if (key === 'reports') loadReportsPage();
  else if (key === 'logs') loadLogsPage();
  else if (key === 'settings') loadSettingsPage();
}

// ── Compact mode ──
let compact = false;
function toggleCompact() {
  compact = !compact;
  document.getElementById('app').classList.toggle('compact', compact);
  document.getElementById('compact-label').textContent = compact ? 'Normal view' : 'Compact view';
}

// ── Connection ──
function setStatus(state) {
  const pill = document.getElementById('status-pill');
  const text = document.getElementById('status-text');
  const dot = pill.querySelector('.dot');
  const connBtn = document.getElementById('connect-btn');
  const scanBtn = document.getElementById('scan-btn');
  const sbDot = document.getElementById('sb-dot');
  const sbConn = document.getElementById('sb-conn-text');
  const sbDev = document.getElementById('sb-device');
  const sbDevSep = document.getElementById('sb-device-sep');
  const devInfo = document.getElementById('device-info');

  pill.className = 'status-pill ' + state;
  dot.className = 'dot' + (state === 'scanning' ? ' pulse' : '');

  if (state === 'disconnected') {
    text.textContent = 'Disconnected';
    connBtn.textContent = 'Connect';
    connBtn.className = 'hdr-btn primary';
    scanBtn.disabled = true;
    scanBtn.textContent = 'SCAN';
    scanBtn.classList.remove('danger');
    sbDot.style.background = 'var(--red)';
    sbConn.textContent = 'Disconnected';
    sbDev.style.display = 'none';
    sbDevSep.style.display = 'none';
    devInfo.style.display = 'none';
  } else if (state === 'connected') {
    text.textContent = 'Connected';
    connBtn.textContent = 'Disconnect';
    connBtn.className = 'hdr-btn danger';
    scanBtn.disabled = false;
    sbDot.style.background = 'var(--green)';
    sbConn.textContent = 'Connected';
    sbDev.style.display = 'flex';
    sbDevSep.style.display = 'block';
    devInfo.style.display = 'block';
  } else if (state === 'scanning') {
    text.textContent = 'Scanning\u2026';
  }
  updateSerialMeta();
}

async function toggleConnect() {
  if (!api()) return;
  if (!connected) {
    const settings = await api().get_settings();
    const port = (settings.com_port || '').trim();
    const baud = Number(settings.baud_rate || 0);
    const autoDetect = !!settings.auto_detect_serial;
    const res = await api().connect(port, baud, autoDetect);
    if (res.connected) {
      connected = true;
      setStatus('connected');
      const meta = res.device_metadata || {};
      document.getElementById('device-info').textContent =
        `${res.port || '?'} \u00b7 ${res.baud || '?'} baud` + (meta.type ? ` \u00b7 ${meta.type}` : '');
      document.getElementById('sb-device').innerHTML = `<span>${res.port || '?'} \u00b7 ${res.baud || '?'} baud</span>`;
      smAppend(`--- Serial port ${res.port || '?'} opened at ${res.baud || '?'} baud ---`, 'serial-sys');
    } else {
      alert('Could not connect: ' + res.message);
    }
  } else {
    await api().disconnect();
    connected = false;
    scanning = false;
    setStatus('disconnected');
    smAppend('--- Serial port closed ---', 'serial-sys');
  }
  refreshConnectedDevicePanel();
}

async function toggleScan() {
  if (!connected || !api()) return;
  scanning = !scanning;
  const btn = document.getElementById('scan-btn');
  if (scanning) {
    const ok = await api().start_scan();
    if (!ok) { scanning = false; return; }
    btn.textContent = 'STOP';
    btn.classList.add('danger');
    setStatus('scanning');
    document.getElementById('scan-name').textContent = 'Waiting for scan\u2026';
    document.getElementById('scan-meta').textContent = 'Place a finger on the sensor.';
    document.getElementById('scan-tag').textContent = 'SCANNING';
    document.getElementById('scan-tag').className = 'scan-status-tag idle';
  } else {
    await api().stop_scan();
    btn.textContent = 'SCAN';
    btn.classList.remove('danger');
    setStatus('connected');
  }
}

function handleConnectionStatus(status) {
  connected = !!status.connected;
  scanning = !!status.scanning;
  setStatus(connected ? (scanning ? 'scanning' : 'connected') : 'disconnected');
  if (connected && status.port) {
    const meta = status.device_metadata || {};
    document.getElementById('device-info').textContent = `${status.port} · ${status.baud || '?'} baud` + (meta.type ? ` · ${meta.type}` : '');
  }
}

function handleModeChanged(payload) {
  scanning = payload.mode === 'scan';
  if (connected) setStatus(scanning ? 'scanning' : 'connected');
}

function handleFingerprintCount(payload) {
  deviceFingerprintCount = Number(payload.count);
  const count = document.getElementById('sb-device-count');
  if (count) count.textContent = `Device fingerprints: ${deviceFingerprintCount}`;
}

function handleScanResult(payload) {
  const student = payload.student || {};
  const name = student.student_name || (payload.status === 'UNKNOWN' ? 'Unknown fingerprint' : `Fingerprint #${payload.fingerprint_id}`);
  const meta = student.student_no
    ? `${student.student_no} \u00b7 Grade ${student.grade || '?'} \u2014 ${student.section || '?'}`
    : (payload.reason || 'No matching student record');
  const now = payload.timestamp ? new Date(payload.timestamp) : new Date();
  const ts = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  document.getElementById('scan-name').textContent = name;
  document.getElementById('scan-meta').textContent = `${meta} \u00b7 ${ts}`;
  const isMatch = !!student.student_no;
  document.getElementById('scan-tag').textContent = isMatch ? (payload.status || 'PRESENT') : 'UNKNOWN';
  document.getElementById('scan-tag').className = 'scan-status-tag ' + (isMatch ? 'present' : 'unknown');
  document.getElementById('scan-icon-wrap').className = 'scan-icon-wrap' + (isMatch ? ' match' : '');
  const confWrap = document.getElementById('conf-wrap');
  if (payload.confidence != null) {
    confWrap.style.display = 'flex';
    document.getElementById('conf-fill').style.width = payload.confidence + '%';
    document.getElementById('conf-label').textContent = payload.confidence + '% confidence';
  } else {
    confWrap.style.display = 'none';
  }

  if (payload.logged) {
    const tbody = document.getElementById('activity-tbody');
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${escapeHtml(now.toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit'}))}</td>` +
      `<td>${escapeHtml(student.student_no || '\u2014')}</td>` +
      `<td>${isMatch ? escapeHtml(student.student_name) : '<em style="color:var(--muted)">Unknown fingerprint</em>'}</td>` +
      `<td>${student.grade ? `Grade ${escapeHtml(student.grade)} \u2014 ${escapeHtml(student.section)}` : '\u2014'}</td>` +
      `<td>${escapeHtml(payload.confidence != null ? payload.confidence + '%' : '\u2014')}</td>` +
      `<td><span class="badge ${isMatch ? 'present' : 'absent'}">${escapeHtml(isMatch ? (payload.status || 'PRESENT') : 'UNKNOWN')}</span></td>`;
    tbody.insertBefore(tr, tbody.firstChild);
    loadDashboardStats();
    attendanceOnScanEvent({
      date: now.toISOString().slice(0, 10),
      time: now.toLocaleTimeString('en-US', { hour12: false }),
      student_no: student.student_no || 'N/A',
      student_name: isMatch ? student.student_name : 'Unregistered',
      grade: student.grade || 'N/A',
      section: student.section || 'N/A',
      confidence: payload.confidence,
      status: isMatch ? (payload.status || 'PRESENT') : 'UNKNOWN',
    });
  }
}

// ── Dashboard ──
async function loadDashboard() {
  await loadDashboardStats();
  await loadRecentActivity();
  const status = await api().get_connection_status();
  connected = status.connected;
  scanning = status.scanning;
  setStatus(connected ? (scanning ? 'scanning' : 'connected') : 'disconnected');
  if (connected) {
    document.getElementById('device-info').textContent = `${status.port || '?'} \u00b7 ${status.baud || '?'} baud`;
  }
}

async function loadDashboardStats() {
  if (!api()) return;
  const stats = await api().get_dashboard_stats();
  document.getElementById('stat-scans').textContent = stats.scans_today;
  document.getElementById('stat-scans-sub').textContent = stats.last_scan_time ? `Last: ${stats.last_scan_time}` : 'No scans yet';
  document.getElementById('stat-students').textContent = stats.total_students;
  document.getElementById('stat-rate').textContent = stats.attendance_rate + '%';
  document.getElementById('stat-rate-sub').textContent =
    (stats.is_fallback ? 'Recent activity' : 'Today') + ` \u2014 ${stats.present_count} of ${stats.total_students}`;
  document.getElementById('stat-unknown').textContent = stats.unknown_scans;
  document.getElementById('sb-students').textContent = `${stats.total_students} students`;
  document.getElementById('sb-scans').textContent = `${stats.scans_today} scans today`;
}

async function loadRecentActivity() {
  const rows = await api().get_recent_activity(25);
  const tbody = document.getElementById('activity-tbody');
  tbody.innerHTML = rows.map(rowToActivityTr).join('');
}

function isKnownRow(r) {
  return !!r.student_no && r.student_no !== 'N/A';
}

function rowToActivityTr(r) {
  const known = isKnownRow(r);
  return `<tr><td>${escapeHtml(r.time || '\u2014')}</td><td>${escapeHtml(known ? r.student_no : '\u2014')}</td>` +
    `<td>${known ? escapeHtml(r.student_name) : '<em style="color:var(--muted)">Unknown fingerprint</em>'}</td>` +
    `<td>${known ? `Grade ${escapeHtml(r.grade)} \u2014 ${escapeHtml(r.section)}` : '\u2014'}</td>` +
    `<td>${escapeHtml(r.confidence != null ? r.confidence + '%' : '\u2014')}</td>` +
    `<td><span class="badge ${badgeClass(r.status)}">${escapeHtml((r.status || 'UNKNOWN').toUpperCase())}</span></td></tr>`;
}

function badgeClass(status) {
  const s = (status || '').toUpperCase();
  if (s.includes('GOOD') || s === 'PRESENT') return 'present';
  if (s === 'LATE') return 'late';
  return 'absent';
}

// ── Attendance ──
let attendanceOffset = 0;
const ATT_PAGE_SIZE = 100;

async function loadAttendancePage() {
  if (!api()) return;
  const mode = document.getElementById('att-mode').value;
  const modeKey = mode === 'Recent' ? 'recent' : mode === 'Last 30 Days' ? 'last30' : 'today';
  const res = await api().get_attendance(modeKey, attendanceOffset);
  renderAttendanceRows(res.rows);
  document.getElementById('att-count').textContent = `${res.rows.length} records`;

  const isRecent = modeKey === 'recent';
  document.getElementById('att-page-sep').style.display = isRecent ? 'block' : 'none';
  document.getElementById('att-prev-btn').style.display = isRecent ? 'inline-flex' : 'none';
  document.getElementById('att-next-btn').style.display = isRecent ? 'inline-flex' : 'none';
  if (isRecent) {
    document.getElementById('att-prev-btn').disabled = attendanceOffset === 0;
    document.getElementById('att-next-btn').disabled = !res.has_more;
  }
}

function renderAttendanceRows(rows) {
  const tbody = document.getElementById('att-tbody');
  tbody.innerHTML = rows.map(r => {
    const known = isKnownRow(r);
    return `<tr><td>${escapeHtml(r.date || '\u2014')}</td><td>${escapeHtml(r.time || '\u2014')}</td><td>${escapeHtml(known ? r.student_no : '\u2014')}</td>` +
      `<td>${known ? escapeHtml(r.student_name) : 'Unknown fingerprint'}</td>` +
      `<td>${known ? `Grade ${escapeHtml(r.grade)} \u2014 ${escapeHtml(r.section)}` : '\u2014'}</td>` +
      `<td>${escapeHtml(r.confidence != null ? r.confidence + '%' : '\u2014')}</td>` +
      `<td><span class="badge ${badgeClass(r.status)}">${escapeHtml((r.status || 'UNKNOWN').toUpperCase())}</span></td></tr>`;
  }).join('');
}

function attendancePrevPage() {
  attendanceOffset = Math.max(0, attendanceOffset - ATT_PAGE_SIZE);
  loadAttendancePage();
}
function attendanceNextPage() {
  attendanceOffset += ATT_PAGE_SIZE;
  loadAttendancePage();
}

document.addEventListener('change', e => {
  if (e.target && e.target.id === 'att-mode') { attendanceOffset = 0; loadAttendancePage(); }
});

// Live: prepend a new row when a scan is logged, without a full reload -
// but only if we're looking at the first page, so a live scan doesn't
// reshuffle rows out from under someone paging through Recent/Today.
function attendanceOnScanEvent(row) {
  const activePage = document.querySelector('.page.active');
  if (!activePage || activePage.id !== 'page-attendance') return;
  if (attendanceOffset !== 0) return;
  const mode = document.getElementById('att-mode').value;
  if (mode === 'Last 30 Days') return;
  const tbody = document.getElementById('att-tbody');
  tbody.insertAdjacentHTML('afterbegin',
    `<tr><td>${escapeHtml(row.date || '')}</td><td>${escapeHtml(row.time || '')}</td><td>${escapeHtml(isKnownRow(row) ? row.student_no : '\u2014')}</td>` +
    `<td>${isKnownRow(row) ? escapeHtml(row.student_name) : 'Unknown fingerprint'}</td>` +
    `<td>${isKnownRow(row) ? `Grade ${escapeHtml(row.grade)} \u2014 ${escapeHtml(row.section)}` : '\u2014'}</td>` +
    `<td>${escapeHtml(row.confidence != null ? row.confidence + '%' : '\u2014')}</td>` +
    `<td><span class="badge ${badgeClass(row.status)}">${escapeHtml((row.status || 'UNKNOWN').toUpperCase())}</span></td></tr>`);
  const countEl = document.getElementById('att-count');
  countEl.textContent = `${tbody.children.length} records`;
}

async function exportAttendanceCsv(mode) {
  if (!api()) return;
  const selected = document.getElementById('att-mode');
  const modeKey = mode || (selected ? (selected.value === 'Recent' ? 'recent' : selected.value === 'Last 30 Days' ? 'last30' : 'today') : 'today');
  const res = await api().export_attendance_csv(modeKey);
  alert(res.ok ? `Exported to:\n${res.path}` : `Export failed: ${res.message}`);
}

// ── Students ──
async function loadStudentsPage() {
  if (!api()) return;
  const students = await api().get_students();
  const tbody = document.getElementById('stu-tbody');
  tbody.innerHTML = students.map(s =>
    `<tr onclick="selectStudent(this, ${Number(s.fingerprint_id)})" style="cursor:pointer">` +
    `<td>${escapeHtml(s.fingerprint_id)}</td><td>${escapeHtml(s.student_no)}</td><td>${escapeHtml(s.student_name)}</td>` +
    `<td>Grade ${escapeHtml(s.grade)}</td><td>${escapeHtml(s.section)}</td></tr>`
  ).join('');
  document.getElementById('stu-count').textContent = `${students.length} students`;
  if (students.length) selectStudent(tbody.firstElementChild, students[0].fingerprint_id);
}

async function selectStudent(row, fingerprintId) {
  document.querySelectorAll('#stu-tbody tr').forEach(r => r.classList.remove('selected-row'));
  if (row) row.classList.add('selected-row');
  const student = await api().get_student(fingerprintId);
  selectedStudent = student;
  if (!student || !student.fingerprint_id) return;
  document.getElementById('det-name').textContent = student.student_name;
  document.getElementById('det-sno').textContent = student.student_no;
  document.getElementById('det-grade').textContent = `Grade ${student.grade}`;
  document.getElementById('det-section').textContent = student.section;
  document.getElementById('det-fpid').textContent = '#' + student.fingerprint_id;
}

let pendingDelete = null; // { fingerprintId, resolve }

async function deleteSelectedStudent() {
  if (!selectedStudent || !selectedStudent.fingerprint_id) return;
  const fpid = selectedStudent.fingerprint_id;
  const name = selectedStudent.student_name;

  if (!connected) {
    alert(`Delete ${name}? Connect to the ESP32 first \u2014 deleting while disconnected is disabled so the database and the sensor can't drift out of sync (a deleted ID could get reused during enrollment while its old fingerprint template is still on the sensor).`);
    return;
  }
  if (!confirm(`Delete ${name}? This will also remove the fingerprint from the connected device.`)) return;

  const res = await api().delete_on_device(fpid);
  if (!res.ok) { alert('Could not delete: ' + res.message); return; }

  const deleted = await waitForDelete(fpid);
  if (deleted) await loadStudentsPage();
}

function waitForDelete(fingerprintId, timeoutMs = 15000) {
  return new Promise(resolve => {
    const timer = setTimeout(() => {
      if (pendingDelete && pendingDelete.fingerprintId === fingerprintId) {
        pendingDelete = null;
        resolve(false);
        alert(`Timed out waiting for the device to delete fingerprint ID ${fingerprintId}. The database was not changed.`);
      }
    }, timeoutMs);
    pendingDelete = {
      fingerprintId,
      resolve: value => { clearTimeout(timer); resolve(value); },
    };
  });
}

function handleDeleteProgress(payload) {
  if (!pendingDelete || payload.id !== pendingDelete.fingerprintId) return;
  if (payload.event === 'success') {
    api().delete_student(pendingDelete.fingerprintId).then(() => {
      pendingDelete.resolve(true);
      pendingDelete = null;
    });
  } else if (payload.event === 'error') {
    alert(`The device reported it could not delete fingerprint ID ${pendingDelete.fingerprintId}. Nothing was removed from the database.`);
    pendingDelete.resolve(false);
    pendingDelete = null;
  }
}

// ── Edit Details (DB-only, no hardware — separate from hardware Enroll) ──
function editSelectedStudentDetails() {
  if (!selectedStudent || !selectedStudent.fingerprint_id) return;
  const s = selectedStudent;
  closeEnrollDialog();
  const overlay = document.createElement('div');
  overlay.id = 'edit-modal-overlay';
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="modal-card">
      <div class="modal-title">Edit Student Details</div>
      <div class="modal-sub">Updates the student record only \u2014 the fingerprint on the device is unchanged.</div>
      <div class="modal-field"><label>Student No.</label><input id="edit-sno" type="text" value="${escapeHtml(s.student_no)}"></div>
      <div class="modal-field"><label>Student Name</label><input id="edit-name" type="text" value="${escapeHtml(s.student_name)}"></div>
      <div class="modal-field-row">
        <div class="modal-field"><label>Grade</label><input id="edit-grade" type="text" value="${escapeHtml(s.grade)}"></div>
        <div class="modal-field"><label>Section</label><input id="edit-section" type="text" value="${escapeHtml(s.section)}"></div>
      </div>
      <div class="modal-status" id="edit-status"></div>
      <div class="modal-actions">
        <button class="hdr-btn" onclick="document.getElementById('edit-modal-overlay').remove()">Cancel</button>
        <button class="hdr-btn primary" onclick="saveEditedStudentDetails(${s.fingerprint_id})">Save</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);
}

async function saveEditedStudentDetails(fingerprintId) {
  const sno = document.getElementById('edit-sno').value.trim();
  const name = document.getElementById('edit-name').value.trim();
  const grade = document.getElementById('edit-grade').value.trim();
  const section = document.getElementById('edit-section').value.trim();
  if (!sno || !name || !grade || !section) {
    document.getElementById('edit-status').textContent = 'Please fill in all fields.';
    return;
  }
  const res = await api().save_student(fingerprintId, sno, name, grade, section);
  if (!res.ok) { document.getElementById('edit-status').textContent = 'Could not save: ' + res.message; return; }
  document.getElementById('edit-modal-overlay').remove();
  await loadStudentsPage();
}

async function wipeAllFingerprints() {
  if (!connected) { alert('Connect to the ESP32 first.'); return; }
  if (!confirm('Wipe ALL fingerprints from the device? This cannot be undone and does not remove student records from the database.')) return;
  const res = await api().wipe_all_on_device();
  if (!res.ok) { alert(res.message); return; }
  const status = document.getElementById('em-status');
  if (status) status.textContent = res.message;
  await new Promise(resolve => {
    const timer = setTimeout(() => {
      window._wipeWait = null;
      resolve();
      alert('Timed out waiting for the device to finish wiping fingerprints.');
    }, 15000);
    window._wipeWait = event => {
      clearTimeout(timer);
      window._wipeWait = null;
      if (event.event === 'error') alert(event.message || 'The device could not wipe fingerprints.');
      else if (event.event === 'success') alert('All fingerprints were removed from the device. Student records were kept.');
      resolve();
    };
  });
}

function handleWipeProgress(payload) {
  if (payload.event === 'success' || payload.event === 'error') {
    if (window._wipeWait) window._wipeWait(payload);
  }
}

// ── Enroll (real hardware flow: device auto-assigns the fingerprint ID) ──
let enrollState = null; // { existing, resolveId }

function reenrollSelectedStudent() {
  if (!selectedStudent || !selectedStudent.fingerprint_id) return;
  openEnrollDialog(selectedStudent);
}

function openEnrollDialog(existing) {
  closeEnrollDialog();
  const overlay = document.createElement('div');
  overlay.id = 'enroll-modal-overlay';
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="modal-card">
      <div class="modal-title">${existing ? 'Re-enroll Fingerprint' : 'Enroll New Student'}</div>
      <div class="modal-sub">${existing ? 'A new fingerprint slot will be assigned by the device.' : 'The device assigns the fingerprint ID automatically \u2014 fill in the student first, then scan.'}</div>
      <div class="modal-field"><label>Student No.</label><input id="em-sno" type="text" value="${existing ? escapeHtml(existing.student_no) : ''}"></div>
      <div class="modal-field"><label>Student Name</label><input id="em-name" type="text" placeholder="Last, First M." value="${existing ? escapeHtml(existing.student_name) : ''}"></div>
      <div class="modal-field-row">
        <div class="modal-field"><label>Grade</label><input id="em-grade" type="text" value="${existing ? escapeHtml(existing.grade) : ''}"></div>
        <div class="modal-field"><label>Section</label><input id="em-section" type="text" value="${existing ? escapeHtml(existing.section) : ''}"></div>
      </div>
      <div class="modal-status" id="em-status">${connected ? '' : 'Connect to the ESP32 first.'}</div>
      <div class="modal-id" id="em-id" style="display:none;"></div>
      <div class="modal-actions">
        <button class="hdr-btn" onclick="closeEnrollDialog()">Cancel</button>
        <button class="hdr-btn primary" id="em-primary-btn" onclick="enrollPrimaryAction()" ${connected ? '' : 'disabled'}>Start Enrollment</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);
  enrollState = { existing: existing || null, assignedId: null, step: 'initial' };
}

function closeEnrollDialog() {
  const overlay = document.getElementById('enroll-modal-overlay');
  if (overlay) overlay.remove();
  if (enrollState && enrollState.step === 'enrolling' && api()) {
    api().cancel_enroll();
  }
  enrollState = null;
}

function enrollPrimaryAction() {
  if (!enrollState) return;
  if (enrollState.step === 'initial') startEnrollment();
  else if (enrollState.step === 'success') saveEnrolledStudent();
}

async function startEnrollment() {
  const sno = document.getElementById('em-sno').value.trim();
  const name = document.getElementById('em-name').value.trim();
  const grade = document.getElementById('em-grade').value.trim();
  const section = document.getElementById('em-section').value.trim();
  if (!sno || !name || !grade || !section) {
    document.getElementById('em-status').textContent = 'Please fill in all student fields first.';
    return;
  }
  enrollState.form = { sno, name, grade, section };

  const btn = document.getElementById('em-primary-btn');
  btn.disabled = true;
  btn.textContent = 'Enrolling\u2026';
  ['em-sno', 'em-name', 'em-grade', 'em-section'].forEach(id => document.getElementById(id).disabled = true);

  const res = await api().start_enroll();
  document.getElementById('em-status').textContent = res.message;
  if (!res.ok) {
    btn.disabled = false;
    btn.textContent = 'Start Enrollment';
    ['em-sno', 'em-name', 'em-grade', 'em-section'].forEach(id => document.getElementById(id).disabled = false);
    return;
  }
  enrollState.step = 'enrolling';
}

function handleEnrollProgress(payload) {
  if (!enrollState || enrollState.step === 'initial') return;
  const status = document.getElementById('em-status');
  const idLabel = document.getElementById('em-id');
  const btn = document.getElementById('em-primary-btn');
  if (!status || !btn) return;

  if (payload.event === 'enrolling') {
    status.textContent = `Enrolling as ID #${payload.id}\u2026 follow the prompts on the sensor.`;
  } else if (payload.event === 'success') {
    enrollState.assignedId = parseInt(payload.id, 10);
    enrollState.step = 'success';
    status.textContent = 'Fingerprint saved on the device.';
    idLabel.style.display = 'block';
    idLabel.textContent = `Assigned ID: #${payload.id}`;
    btn.disabled = false;
    btn.textContent = 'Save Student';
  } else if (payload.event === 'cancelled') {
    status.textContent = 'Enrollment was cancelled on the device.';
    resetEnrollForm();
  } else if (payload.event === 'error') {
    status.textContent = 'The device reported an enrollment error.';
    resetEnrollForm();
  }
}

function resetEnrollForm() {
  const btn = document.getElementById('em-primary-btn');
  if (!btn) return;
  btn.disabled = false;
  btn.textContent = 'Start Enrollment';
  ['em-sno', 'em-name', 'em-grade', 'em-section'].forEach(id => document.getElementById(id).disabled = false);
  if (enrollState) enrollState.step = 'initial';
}

async function saveEnrolledStudent() {
  if (!enrollState || !enrollState.assignedId || !enrollState.form) return;
  const { sno, name, grade, section } = enrollState.form;
  const newId = enrollState.assignedId;
  const previous = enrollState.existing;

  const res = await api().save_student(newId, sno, name, grade, section);
  if (!res.ok) {
    document.getElementById('em-status').textContent = 'Could not save: ' + res.message;
    return;
  }

  // Re-enroll: the device assigned a new slot, so retire the old one instead
  // of leaving a stale duplicate row (and a stale template still on the
  // sensor for that old ID).
  if (previous && previous.fingerprint_id && previous.fingerprint_id !== newId) {
    const del = await api().delete_on_device(previous.fingerprint_id);
    if (!del.ok) {
      document.getElementById('em-status').textContent = `Saved new fingerprint, but the old device record could not be removed: ${del.message}`;
      return;
    }
    const deleted = await waitForDelete(previous.fingerprint_id);
    if (!deleted) {
      document.getElementById('em-status').textContent = 'New fingerprint saved, but the old fingerprint remains on the device. Review the student records before continuing.';
      return;
    }
    await api().delete_student(previous.fingerprint_id);
  }

  closeEnrollDialog();
  await loadStudentsPage();
  api().request_fingerprint_count();
}

async function exportStudentsCsv() {
  const res = await api().export_students_csv();
  alert(res.ok ? `Exported to:\n${res.path}` : `Export failed: ${res.message}`);
}

// ── Reports ──
async function loadReportsPage() {
  if (!api()) return;
  await generateStatsReport();
  await loadBackupsList();
  const stats = await api().get_dashboard_stats();
  document.getElementById('rpt-today-count').textContent = `${stats.scans_today} scans`;
  document.getElementById('rpt-students-count').textContent = `${stats.total_students} records`;
  document.getElementById('rpt-last30-label').textContent = new Date().toLocaleString('en-US', { month: 'long', year: 'numeric' });
}

async function generateStatsReport() {
  const report = await api().get_statistics_report();
  const now = new Date();
  const ts = now.toLocaleString('en-PH', { year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const rankClass = i => i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : '';
  const maxCnt = report.top_students.length ? report.top_students[0].count : 1;
  const totalGraded = Object.values(report.by_grade).reduce((a, b) => a + b, 0) || 1;

  const div = document.getElementById('stats-report');
  div.innerHTML = `
    <div class="rpt-root">
      <div class="rpt-metrics">
        <div class="rpt-metric blue">
          <div class="rpt-metric-label">Total Students</div>
          <div class="rpt-metric-value">${report.total_students}</div>
          <div class="rpt-metric-sub">Enrolled fingerprints</div>
        </div>
        <div class="rpt-metric green">
          <div class="rpt-metric-label">Attendance Records</div>
          <div class="rpt-metric-value">${report.total_records}</div>
          <div class="rpt-metric-sub">Across all students</div>
        </div>
        <div class="rpt-metric yellow">
          <div class="rpt-metric-label">Avg per Student</div>
          <div class="rpt-metric-value">${report.avg_per_student}</div>
          <div class="rpt-metric-sub">Records per enrolled student</div>
        </div>
      </div>

      <div class="rpt-section-block">
        <div class="rpt-section-title">Top Students \u2014 By Attendance Count</div>
        <div class="rpt-ts-line">Generated ${ts}</div>
        <table class="rpt-table">
          <thead><tr><th style="width:32px">#</th><th>Name</th><th>Student No.</th><th>Grade</th><th>Section</th><th class="rpt-bar-cell">Attendance</th></tr></thead>
          <tbody>
            ${report.top_students.map((s, i) => `
            <tr>
              <td><span class="rpt-rank ${rankClass(i)}">${i + 1}</span></td>
              <td>${escapeHtml(s.student_name)}</td>
              <td style="color:var(--muted2);font-size:12px;">${escapeHtml(s.student_no || '\u2014')}</td>
              <td style="color:var(--muted2);">${escapeHtml(s.grade || '\u2014')}</td>
              <td style="color:var(--muted2);">${escapeHtml(s.section || '\u2014')}</td>
              <td class="rpt-bar-cell">
                <div class="rpt-bar-wrap">
                  <div class="rpt-bar-bg"><div class="rpt-bar-fill" style="width:${Math.round(s.count / maxCnt * 100)}%"></div></div>
                  <span class="rpt-bar-label">${s.count}</span>
                </div>
              </td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>

      <div class="rpt-section-block">
        <div class="rpt-section-title">Students by Grade</div>
        <table class="rpt-table">
          <thead><tr><th>Grade</th><th>Students</th><th class="rpt-bar-cell">Distribution</th></tr></thead>
          <tbody>
            ${Object.entries(report.by_grade).map(([g, n]) => `
            <tr>
              <td>${escapeHtml(g)}</td><td>${escapeHtml(n)}</td>
              <td class="rpt-bar-cell">
                <div class="rpt-bar-wrap">
                  <div class="rpt-bar-bg"><div class="rpt-bar-fill" style="width:${Math.round(n / totalGraded * 100)}%;background:var(--green)"></div></div>
                  <span class="rpt-bar-label">${Math.round(n / totalGraded * 100)}%</span>
                </div>
              </td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>

      <div class="rpt-section-block">
        <div class="rpt-section-title">All Enrolled Students</div>
        <table class="rpt-table">
          <thead><tr><th>Name</th><th>Student No.</th><th>Grade</th><th>Section</th><th>Records</th></tr></thead>
          <tbody>
            ${report.all_students.map(s => `
            <tr>
              <td>${escapeHtml(s.student_name)}</td>
              <td style="color:var(--muted2);font-size:12px;">${escapeHtml(s.student_no || '\u2014')}</td>
              <td style="color:var(--muted2);">${escapeHtml(s.grade || '\u2014')}</td>
              <td style="color:var(--muted2);">${escapeHtml(s.section || '\u2014')}</td>
              <td><span class="badge present">${escapeHtml(s.count)}</span></td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    </div>`;
}

async function loadBackupsList() {
  const backups = await api().list_backups();
  const div = document.getElementById('backups-list');
  if (!backups.length) {
    div.innerHTML = '<div class="report-item"><span class="report-name" style="color:var(--muted)">No backups yet</span></div>';
    return;
  }
  div.innerHTML = backups.map(b => {
    return `<div class="report-item" style="cursor:pointer" onclick="restoreBackup('${b.path.replace(/\\/g, '\\\\')}')">` +
      `<span class="report-icon">\u{1F4BE}</span><span class="report-name">${escapeHtml(b.name)}</span>` +
      `<span class="report-meta">${escapeHtml(b.date || '')} \u00b7 ${escapeHtml(b.size_mb || '?')}</span></div>`;
  }).join('');
}

async function createBackupNow() {
  const res = await api().create_backup();
  alert(res.ok ? res.message : `Backup failed: ${res.message}`);
  loadBackupsList();
}

async function restoreBackup(path) {
  if (!confirm('Restore this backup? The current database will be overwritten.')) return;
  const res = await api().restore_backup(path);
  alert(res.ok ? 'Database restored.' : `Restore failed: ${res.message}`);
  if (res.ok) {
    selectedStudent = null;
    await Promise.all([loadDashboard(), loadAttendancePage(), loadStudentsPage(), loadReportsPage(), loadSettingsPage()]);
    if (connected) api().request_fingerprint_count();
  }
}

// ── Logs ──
async function loadLogsPage() {
  if (!api()) return;
  const lines = await api().get_app_log(500);
  const out = document.getElementById('applog-output');
  out.innerHTML = lines.map(parseLogLine).join('');
  out.scrollTop = out.scrollHeight;
  applyAppLogFilter();
  updateSerialMeta();
}

function parseLogLine(line) {
  // Format written by core/logger.py: "YYYY-mm-dd HH:MM:SS.ffffff | LEVEL   | SRC | message"
  const parts = line.split(' | ');
  const ts = parts[0] || '';
  const lvl = (parts[1] || 'INFO').trim();
  const src = parts[2] || 'SYSTEM';
  const msg = parts.slice(3).join(' | ');
  const lvlClass = lvl === 'SUCCESS' ? 'ok' : lvl === 'WARNING' || lvl === 'WARN' ? 'warn' : lvl === 'ERROR' || lvl === 'CRITICAL' ? 'err' : 'info';
  return `<div class="log-line" data-lvl="${escapeHtml(lvl)}"><span class="log-ts">${escapeHtml(ts)}</span><span class="log-lvl ${lvlClass}">${escapeHtml(lvl.padEnd(7, '\u00a0'))}</span><span class="log-src">${escapeHtml(src)}</span><span class="log-msg">${escapeHtml(msg)}</span></div>`;
}

function applyAppLogFilter() {
  const lvl = document.getElementById('applog-filter').value;
  const q = document.getElementById('applog-search').value.toLowerCase();
  document.querySelectorAll('#applog-output .log-line').forEach(row => {
    const lvlMatch = lvl === 'all' || row.dataset.lvl === lvl;
    const qMatch = !q || row.textContent.toLowerCase().includes(q);
    row.classList.toggle('hidden', !(lvlMatch && qMatch));
  });
}
function clearAppLog() { document.getElementById('applog-output').innerHTML = ''; }

// Live push from Api._push('log_line', ...) — every line logged this run
// arrives here as it happens, so the page stays current without needing to
// be re-navigated to. Only touches the DOM if the Logs page actually exists
// (it's always in the DOM, just possibly not the active page).
const MAX_LOG_ROWS = 1500;
function appendLiveLogLine(line) {
  const out = document.getElementById('applog-output');
  if (!out) return;
  const template = document.createElement('template');
  template.innerHTML = parseLogLine(line);
  const row = template.content.firstElementChild;
  out.appendChild(row);

  const lvl = document.getElementById('applog-filter').value;
  const q = document.getElementById('applog-search').value.toLowerCase();
  const lvlMatch = lvl === 'all' || row.dataset.lvl === lvl;
  const qMatch = !q || row.textContent.toLowerCase().includes(q);
  row.classList.toggle('hidden', !(lvlMatch && qMatch));

  while (out.children.length > MAX_LOG_ROWS) out.removeChild(out.firstElementChild);

  const activePage = document.querySelector('.page.active');
  if (activePage && activePage.id === 'page-logs') out.scrollTop = out.scrollHeight;
}

// ── Serial Monitor ──
let serialPaused = false;
let serialBuffer = [];
function smAppend(text, cls) {
  const entry = { text, cls };
  if (serialPaused) { serialBuffer.push(entry); return; }
  _smWrite(text, cls);
}
function _smWrite(text, cls) {
  const out = document.getElementById('serial-output');
  if (!out) return;
  const div = document.createElement('div');
  div.className = cls || 'serial-rx';
  div.textContent = text;
  out.appendChild(div);
  const autoscroll = document.getElementById('sm-autoscroll');
  if (autoscroll && autoscroll.checked) out.scrollTop = out.scrollHeight;
}
function toggleSerialPause() {
  serialPaused = !serialPaused;
  const btn = document.getElementById('sm-pause-btn');
  btn.textContent = serialPaused ? 'Resume' : 'Pause';
  btn.classList.toggle('primary', serialPaused);
  if (!serialPaused) { serialBuffer.forEach(e => _smWrite(e.text, e.cls)); serialBuffer = []; }
}
function clearSerial() { document.getElementById('serial-output').innerHTML = ''; serialBuffer = []; }

async function serialCmd(cmd) {
  if (!connected) return;
  await api().send_serial_command(cmd);
}
async function sendSerialCmd() {
  const input = document.getElementById('serial-cmd');
  const val = input.value.trim();
  if (!val || !connected) return;
  input.value = '';
  await api().send_serial_command(val);
}
document.addEventListener('keydown', e => {
  if (e.key === 'Enter' && document.activeElement.id === 'serial-cmd') sendSerialCmd();
});

async function updateSerialMeta() {
  const port = document.getElementById('sm-port');
  const baud = document.getElementById('sm-baud');
  const state = document.getElementById('sm-state');
  if (!port || !baud || !state) return;
  if (connected && api()) {
    const status = await api().get_connection_status();
    port.textContent = `Port: ${status.port || 'N/A'}`;
    baud.textContent = `Baud: ${status.baud || 'N/A'}`;
    state.textContent = 'State: Connected';
    state.className = 'sm-state connected';
  } else {
    port.textContent = 'Port: N/A';
    baud.textContent = 'Baud: N/A';
    state.textContent = 'State: Disconnected';
    state.className = 'sm-state disconnected';
  }
}

// ── Draggable resize between log panels ──
(function () {
  const handle = document.getElementById('log-resize-handle');
  if (!handle) return;
  let dragging = false, startY = 0, startTop = 0;
  handle.addEventListener('mousedown', e => {
    dragging = true;
    startY = e.clientY;
    const panels = document.querySelectorAll('.log-panel');
    startTop = panels[0].getBoundingClientRect().height;
    handle.classList.add('dragging');
    e.preventDefault();
  });
  document.addEventListener('mousemove', e => {
    if (!dragging) return;
    const page = document.getElementById('page-logs');
    const total = page.getBoundingClientRect().height - handle.offsetHeight;
    const delta = e.clientY - startY;
    const newTop = Math.max(60, Math.min(total - 120, startTop + delta));
    const panels = document.querySelectorAll('.log-panel');
    panels[0].style.flex = 'none';
    panels[0].style.height = newTop + 'px';
    panels[1].style.flex = '1';
    panels[1].style.height = '';
  });
  document.addEventListener('mouseup', () => { dragging = false; handle.classList.remove('dragging'); });
})();

function applyTheme(theme) {
  const t = (theme || 'dark').toLowerCase();
  document.body.classList.toggle('light-theme', t === 'light');
  const select = document.getElementById('set-theme');
  if (select) select.value = t;
}
async function loadSettingsPage() {
  if (!api()) return;
  const s = await api().get_settings();
  document.getElementById('set-auto-reconnect').classList.toggle('on', !!s.auto_reconnect);
  document.getElementById('set-auto-detect').classList.toggle('on', !!s.auto_detect_serial);
  applyTheme(s.theme);
  document.getElementById('settings-compact-toggle').classList.toggle('on', !!s.compact_sidebar);
  document.getElementById('set-cooldown').value = s.cooldown;
  document.getElementById('set-confidence').value = s.min_confidence;
  document.getElementById('role-select').value = s.current_role || 'admin';
  currentRole = s.current_role || 'admin';
  applyRole(currentRole);
  document.getElementById('set-log-to-file').classList.toggle('on', !!s.log_to_file);
  document.getElementById('set-debug-logging').classList.toggle('on', !!s.enable_debug_logging);
  document.getElementById('set-log-folder').textContent = s.log_folder || '\u2014';
  document.getElementById('set-backup-interval').value = s.auto_backup_interval_minutes;
  document.getElementById('set-last-backup').textContent = s.last_backup || 'No backups yet';

  await refreshConnectedDevicePanel();
  await refreshPortList();
  populateBaudOptions(s.baud_rate);
  const portInput = document.getElementById('set-port-override');
  if (portInput) portInput.value = s.com_port || '';
}

async function refreshConnectedDevicePanel() {
  const status = await api().get_connection_status();
  const pill = document.getElementById('conn-device-status');
  const detail = document.getElementById('conn-device-detail');
  if (status.connected) {
    pill.textContent = '\u25cf Connected';
    pill.className = 'conn-status-pill connected';
    const meta = status.device_metadata || {};
    const lines = [];
    if (status.port) lines.push(`Port: ${status.port}`);
    if (status.baud) lines.push(`Baud: ${status.baud}`);
    if (meta.device) lines.push(`Device: ${meta.device}`);
    if (meta.board) lines.push(`Board: ${meta.board}`);
    if (meta.firmware) lines.push(`Firmware: ${meta.firmware}`);
    if (meta.protocol !== undefined && meta.protocol !== null) lines.push(`Protocol: ${meta.protocol}`);
    if (meta.sensor) lines.push(`Sensor: ${meta.sensor}`);
    if (meta.serial_number) lines.push(`Serial Number: ${meta.serial_number}`);
    detail.textContent = lines.length ? lines.join('\n') : 'Connected, but the device hasn\u2019t reported its metadata yet.';
  } else {
    pill.textContent = '\u25cf Disconnected';
    pill.className = 'conn-status-pill';
    detail.textContent = 'No device connected yet. Connect from the top bar \u2014 this panel will fill in automatically once a device responds.';
  }
}

async function refreshPortList() {
  const ports = await api().list_ports_detailed();
  const datalist = document.getElementById('conn-port-list');
  datalist.innerHTML = ports.map(p => `<option value="${escapeHtml(p.device)}">${escapeHtml(p.label)}</option>`).join('');
  document.getElementById('conn-port-count').textContent = `Devices found: ${ports.length}`;
}

async function forgetSavedPort() {
  await api().forget_saved_port();
  document.getElementById('set-port-override').value = '';
  alert('Saved port cleared. The app will auto-detect the ESP32 on next connect.');
}

function populateBaudOptions(current) {
  const select = document.getElementById('set-baud-rate-select');
  const rates = [9600, 19200, 38400, 57600, 115200, 230400];
  select.innerHTML = rates.map(r => `<option value="${r}">${r}</option>`).join('');
  select.value = current || 115200;
}

async function saveSettings() {
  const payload = {
    com_port: document.getElementById('set-port-override').value.trim(),
    baud_rate: parseInt(document.getElementById('set-baud-rate-select').value, 10),
    theme: document.getElementById('set-theme').value,
    auto_reconnect: document.getElementById('set-auto-reconnect').classList.contains('on'),
    auto_detect_serial: document.getElementById('set-auto-detect').classList.contains('on'),
    compact_sidebar: document.getElementById('settings-compact-toggle').classList.contains('on'),
    cooldown: parseInt(document.getElementById('set-cooldown').value, 10),
    min_confidence: parseInt(document.getElementById('set-confidence').value, 10),
    log_to_file: document.getElementById('set-log-to-file').classList.contains('on'),
    enable_debug_logging: document.getElementById('set-debug-logging').classList.contains('on'),
    auto_backup_interval_minutes: parseInt(document.getElementById('set-backup-interval').value, 10),
  };
  const res = await api().save_ui_settings(payload);
  if (!res.ok) { alert(`Settings could not be saved: ${res.message}`); return; }
  compact = payload.compact_sidebar;
  document.getElementById('app').classList.toggle('compact', compact);
  alert('Settings saved.');
}

function openLogFolder() { api().open_log_folder(); }

// ── User Role ──
const ROLE_COLORS = {
  scan: '#1E3A5F:#60A5FA', enroll: '#14532D:#4ADE80', delete: '#7F1D1D:#FCA5A5',
  wipe: '#7F1D1D:#FCA5A5', export: '#1A1F0A:#A3E635', backup: '#1e1b4b:#a5b4fc',
  restore: '#1e1b4b:#a5b4fc',
};
const ROLE_LABELS = { admin: 'Administrator', teacher: 'Teacher', guest: 'Guest' };

function paintTitlebarRole(key) {
  const badge = document.getElementById('titlebar-role');
  if (!badge) return;
  badge.className = 'tb-role-badge role-' + key;
  badge.value = key;
}

async function applyRole(key) {
  const res = await api().set_current_role(key);
  currentRole = key;
  paintTitlebarRole(key);
  const select = document.getElementById('role-select');
  if (select) select.value = key;
  const wrap = document.getElementById('role-permissions');
  if (wrap) {
    wrap.innerHTML = (res.permissions || []).map(p => {
      const [bg, fg] = (ROLE_COLORS[p] || '#1F2229:#9CA3AF').split(':');
      return `<span style="display:inline-block;padding:2px 9px;border-radius:3px;font-size:11px;font-weight:600;background:${bg};color:${fg};">${p}</span>`;
    }).join('');
  }
  const permissions = new Set(res.permissions || []);
  const studentsNav = document.querySelector('[onclick*="nav(this,\'students\')"]');
  const reportsNav = document.querySelector('[onclick*="nav(this,\'reports\')"]');
  if (studentsNav) studentsNav.style.display = permissions.has('enroll') || permissions.has('delete') ? 'flex' : 'none';
  if (reportsNav) reportsNav.style.display = permissions.has('export') || permissions.has('backup') || permissions.has('restore') ? 'flex' : 'none';
  document.querySelectorAll('[data-permission]').forEach(element => {
    element.disabled = !permissions.has(element.dataset.permission);
  });
}

function updateRole() {
  const key = document.getElementById('role-select').value;
  applyRole(key);
}

// ── Clock ──
function tick() {
  const now = new Date();
  document.getElementById('sb-time').textContent =
    now.toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' }) + ' \u00b7 ' +
    now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// ── Table filter (search boxes) ──
function filterTable(tbodyId, inputId) {
  const q = document.getElementById(inputId).value.toLowerCase();
  document.querySelectorAll('#' + tbodyId + ' tr').forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

// ── Boot ──
tick();
setInterval(tick, 1000);
whenApiReady(() => {
  loadDashboard();
  api().get_settings().then(s => applyTheme(s.theme));
  api().get_current_role().then(role => { currentRole = role || 'admin'; paintTitlebarRole(currentRole); });
  // Lightweight background refresh so the dashboard/logs pages stay current
  // even if the scan callback happens while the user is on another page.
  connectionPollTimer = setInterval(async () => {
    if (!api()) return;
    const status = await api().get_connection_status();
    handleConnectionStatus(status);
    const activePage = document.querySelector('.page.active');
    if (activePage && activePage.id === 'page-dashboard') loadDashboardStats();
  }, 5000);
});
