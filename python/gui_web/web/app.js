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
    const res = await api().connect('', 0, true);
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
    tr.innerHTML = `<td>${now.toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit'})}</td>` +
      `<td>${student.student_no || '\u2014'}</td>` +
      `<td>${isMatch ? student.student_name : '<em style="color:var(--muted)">Unknown fingerprint</em>'}</td>` +
      `<td>${student.grade ? `Grade ${student.grade} \u2014 ${student.section}` : '\u2014'}</td>` +
      `<td>${payload.confidence != null ? payload.confidence + '%' : '\u2014'}</td>` +
      `<td><span class="badge ${isMatch ? 'present' : 'absent'}">${isMatch ? (payload.status || 'PRESENT') : 'UNKNOWN'}</span></td>`;
    tbody.insertBefore(tr, tbody.firstChild);
    loadDashboardStats();
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
  return `<tr><td>${r.time || '\u2014'}</td><td>${known ? r.student_no : '\u2014'}</td>` +
    `<td>${known ? r.student_name : '<em style="color:var(--muted)">Unknown fingerprint</em>'}</td>` +
    `<td>${known ? `Grade ${r.grade} \u2014 ${r.section}` : '\u2014'}</td>` +
    `<td>${r.confidence != null ? r.confidence + '%' : '\u2014'}</td>` +
    `<td><span class="badge ${badgeClass(r.status)}">${(r.status || 'UNKNOWN').toUpperCase()}</span></td></tr>`;
}

function badgeClass(status) {
  const s = (status || '').toUpperCase();
  if (s.includes('GOOD') || s === 'PRESENT') return 'present';
  if (s === 'LATE') return 'late';
  return 'absent';
}

// ── Attendance ──
async function loadAttendancePage() {
  if (!api()) return;
  const mode = document.getElementById('att-mode').value;
  const modeKey = mode === 'Recent' ? 'recent' : mode === 'Last 30 Days' ? 'last30' : 'today';
  const rows = await api().get_attendance(modeKey);
  const tbody = document.getElementById('att-tbody');
  tbody.innerHTML = rows.map(r => {
    const known = isKnownRow(r);
    return `<tr><td>${r.date || '\u2014'}</td><td>${r.time || '\u2014'}</td><td>${known ? r.student_no : '\u2014'}</td>` +
      `<td>${known ? r.student_name : 'Unknown fingerprint'}</td>` +
      `<td>${known ? `Grade ${r.grade} \u2014 ${r.section}` : '\u2014'}</td>` +
      `<td>${r.confidence != null ? r.confidence + '%' : '\u2014'}</td>` +
      `<td><span class="badge ${badgeClass(r.status)}">${(r.status || 'UNKNOWN').toUpperCase()}</span></td></tr>`;
  }).join('');
  document.getElementById('att-count').textContent = `${rows.length} records`;
}
document.addEventListener('change', e => { if (e.target && e.target.id === 'att-mode') loadAttendancePage(); });

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
    `<tr onclick="selectStudent(this, ${s.fingerprint_id})" style="cursor:pointer">` +
    `<td>${s.fingerprint_id}</td><td>${s.student_no}</td><td>${s.student_name}</td>` +
    `<td>Grade ${s.grade}</td><td>${s.section}</td></tr>`
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

async function deleteSelectedStudent() {
  if (!selectedStudent || !selectedStudent.fingerprint_id) return;
  if (!confirm(`Delete ${selectedStudent.student_name}? This cannot be undone.`)) return;
  const res = await api().delete_student(selectedStudent.fingerprint_id);
  if (!res.ok) { alert('Could not delete: ' + res.message); return; }
  await loadStudentsPage();
}

function reenrollSelectedStudent() {
  if (!selectedStudent || !selectedStudent.fingerprint_id) return;
  openEnrollDialog(selectedStudent);
}

function openEnrollDialog(existing) {
  const fpid = prompt('Fingerprint ID (1-127):', existing ? existing.fingerprint_id : '');
  if (!fpid) return;
  const studentNo = prompt('Student No.:', existing ? existing.student_no : '');
  if (studentNo === null) return;
  const studentName = prompt('Student Name (Last, First M.):', existing ? existing.student_name : '');
  if (studentName === null) return;
  const grade = prompt('Grade:', existing ? existing.grade : '');
  if (grade === null) return;
  const section = prompt('Section:', existing ? existing.section : '');
  if (section === null) return;

  api().save_student(parseInt(fpid, 10), studentNo, studentName, grade, section).then(res => {
    if (!res.ok) { alert('Could not save: ' + res.message); return; }
    loadStudentsPage();
  });
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
              <td>${s.student_name}</td>
              <td style="color:var(--muted2);font-size:12px;">${s.student_no || '\u2014'}</td>
              <td style="color:var(--muted2);">${s.grade || '\u2014'}</td>
              <td style="color:var(--muted2);">${s.section || '\u2014'}</td>
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
              <td>${g}</td><td>${n}</td>
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
              <td>${s.student_name}</td>
              <td style="color:var(--muted2);font-size:12px;">${s.student_no || '\u2014'}</td>
              <td style="color:var(--muted2);">${s.grade || '\u2014'}</td>
              <td style="color:var(--muted2);">${s.section || '\u2014'}</td>
              <td><span class="badge present">${s.count}</span></td>
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
      `<span class="report-icon">\u{1F4BE}</span><span class="report-name">${b.name}</span>` +
      `<span class="report-meta">${b.date || ''} \u00b7 ${b.size_mb || '?'}</span></div>`;
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
  if (res.ok) { loadDashboardStats(); loadReportsPage(); }
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
  return `<div class="log-line" data-lvl="${lvl}"><span class="log-ts">${ts}</span><span class="log-lvl ${lvlClass}">${lvl.padEnd(7, '\u00a0')}</span><span class="log-src">${src}</span><span class="log-msg">${msg}</span></div>`;
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

function updateSerialMeta() {
  const port = document.getElementById('sm-port');
  const baud = document.getElementById('sm-baud');
  const state = document.getElementById('sm-state');
  if (!port || !baud || !state) return;
  if (connected) {
    port.textContent = `Port: ${document.getElementById('device-info').textContent.split('\u00b7')[0].trim() || 'N/A'}`;
    baud.textContent = 'Baud: connected';
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
  datalist.innerHTML = ports.map(p => `<option value="${p.device}">${p.label}</option>`).join('');
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
  await api().save_ui_settings(payload);
  alert('Settings saved. Some changes take effect on next launch.');
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
  setInterval(() => {
    const activePage = document.querySelector('.page.active');
    if (activePage && activePage.id === 'page-dashboard') loadDashboardStats();
  }, 5000);
});
