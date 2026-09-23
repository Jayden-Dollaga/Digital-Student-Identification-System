// DSIS v3 — frontend logic. Talks to Python exclusively through
// `window.pywebview.api` (see python/gui_web/api.py). No mock/sample data
// lives here — every table, stat, and status pill is populated from a real
// backend call.

const PAGE_TITLES = {
  dashboard: 'Dashboard', attendance: 'Attendance', students: 'Students',
  reports: 'Reports', logs: 'Logs', settings: 'Settings', calendar: 'Calendar',
};

let connected = false;
let connectAttemptInFlight = false;
let scanning = false;
let selectedStudent = null;
const selectedStudentIds = new Set();
const studentNames = new Map();
let batchDeletePending = null;
let batchDeleteResult = null;
let currentRole = 'guest';
let currentPermissions = new Set(['scan']);
let pendingRole = null;
let sessionTouchTimer = null;
const ROLE_LEVELS = { guest: 0, teacher: 1, admin: 2 };
let deviceFingerprintCount = null;
let connectionPollTimer = null;

function hasPermission(action) {
  return currentPermissions.has(action);
}

function hasRole(requiredRole) {
  return (ROLE_LEVELS[currentRole] || 0) >= (ROLE_LEVELS[requiredRole] || 99);
}

function refreshAdminOnlyVisibility() {
  const isAdmin = currentRole === 'admin' && hasRole('admin');
  document.querySelectorAll('[data-admin-only-rfid]').forEach(element => {
    element.style.display = isAdmin ? 'block' : 'none';
  });
}

function guardPermission(action, label) {
  if (!hasPermission(action)) {
    alert(`${label || 'This action'} requires the ${action} permission for the current role.`);
    return false;
  }
  return true;
}

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
  else if (event === 'connection_changed') handleConnectionChanged(payload);
  else if (event === 'connection_troubleshooting') showSerialTroubleshooting(payload.reason);
  else if (event === 'serial_error') handleSerialError(payload);
  else if (event === 'data_changed') handleDataChanged(payload);
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
  else if (key === 'settings') {
    refreshAdminOnlyVisibility();
    loadSettingsPage();
  }
  else if (key === 'calendar') loadCalendarPage();
}

function applySessionState(state) {
  if (!state || !state.ok) return;
  const roleKey = String(state.role || 'guest').toLowerCase();
  currentRole = roleKey === 'administrator' ? 'admin' : roleKey;
  currentPermissions = new Set(state.permissions || ['scan']);
  paintTitlebarRole(currentRole);
  const titlebar = document.getElementById('titlebar-role');
  if (titlebar) titlebar.value = currentRole;
  const select = document.getElementById('role-select');
  if (select) select.value = currentRole;
  const wrap = document.getElementById('role-permissions');
  if (wrap) {
    wrap.innerHTML = [...currentPermissions].map(p =>
      `<span class="role-permission role-permission-${escapeHtml(p)}">${escapeHtml(p)}</span>`
    ).join('');
  }
  const scanBtn = document.getElementById('scan-btn');
  if (scanBtn) scanBtn.disabled = !hasPermission('scan') || !connected;
  const studentsNav = document.querySelector('[onclick*="nav(this,\'students\')"]');
  const reportsNav = document.querySelector('[onclick*="nav(this,\'reports\')"]');
  const calendarNav = document.querySelector('[onclick*="nav(this,\'calendar\')"]');
  const canUseStudents = hasPermission('enroll') || hasPermission('delete') || hasPermission('wipe');
  const canUseReports = hasPermission('export') || hasPermission('backup') || hasPermission('restore');
  const canUseCalendar = hasPermission('manage_calendar');
  if (studentsNav) studentsNav.style.display = canUseStudents ? 'flex' : 'none';
  if (reportsNav) reportsNav.style.display = canUseReports ? 'flex' : 'none';
  if (calendarNav) calendarNav.style.display = canUseCalendar ? 'flex' : 'none';
  const activePage = document.querySelector('.page.active');
  if (activePage && ((activePage.id === 'page-students' && !canUseStudents) ||
      (activePage.id === 'page-reports' && !canUseReports) ||
      (activePage.id === 'page-calendar' && !canUseCalendar))) {
    const dashboardNav = document.querySelector('[onclick*="nav(this,\'dashboard\')"]');
    if (dashboardNav) nav(dashboardNav, 'dashboard');
  }
  document.querySelectorAll('[data-required-role]').forEach(element => {
    const allowed = hasRole(element.dataset.requiredRole);
    element.classList.toggle('settings-locked', !allowed);
    element.querySelectorAll('input, select, button, .toggle-switch').forEach(control => {
      control.disabled = !allowed;
      control.style.pointerEvents = allowed ? '' : 'none';
      control.style.opacity = allowed ? '1' : '0.45';
    });
  });
  refreshAdminOnlyVisibility();
  document.querySelectorAll('[data-permission]').forEach(element => {
    const allowed = hasPermission(element.dataset.permission);
    element.disabled = !allowed;
    element.style.opacity = allowed ? '1' : '0.45';
    element.title = allowed ? '' : `Requires ${element.dataset.permission} permission`;
  });
}

// Toggles a password input between hidden/visible. Bound via a plain
// onclick attribute on a real button (not addEventListener), so it's
// re-evaluated fresh on every click - it can't go stale or stop responding
// after one use the way the browser's native reveal-password icon did.
function togglePasswordField(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const showing = input.type === 'text';
  input.type = showing ? 'password' : 'text';
  btn.textContent = showing ? 'Show' : 'Hide';
  btn.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
}

const WIZARD_STEPS = [
  { key: 'password', label: 'Password' },
  { key: 'device', label: 'Device' },
  { key: 'schedule', label: 'Schedule' },
  { key: 'branding', label: 'Finish' },
];

// Renders a Huawei-router-style step progress bar (circles connected by a
// line, current step highlighted, completed steps checked) into the given
// container id. Called once per step-open so it always reflects where the
// user currently is.
function renderWizardProgress(containerId, activeKey) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const activeIndex = WIZARD_STEPS.findIndex(s => s.key === activeKey);
  let html = '<div class="wizard-progress-row">';
  WIZARD_STEPS.forEach((step, i) => {
    const state = i < activeIndex ? 'done' : i === activeIndex ? 'active' : 'upcoming';
    html += `<div class="wizard-progress-step wizard-step-${state}">
      <div class="wizard-progress-circle">${state === 'done' ? '\u2713' : i + 1}</div>
      <div class="wizard-progress-label">${escapeHtml(step.label)}</div>
    </div>`;
    if (i < WIZARD_STEPS.length - 1) {
      html += `<div class="wizard-progress-line${i < activeIndex ? ' wizard-line-done' : ''}"></div>`;
    }
  });
  html += '</div>';
  container.innerHTML = html;
}

// "Previous" only ever targets device/schedule (never password - once the
// administrator account is created there's nothing to go "back" to, the
// wizard router would just send them right back to this step anyway).
function wizardGoToPreviousStep(targetKey) {
  ['first-run-setup-modal', 'setup-device-modal', 'setup-schedule-modal', 'setup-branding-modal'].forEach(id => {
    const modal = document.getElementById(id);
    if (modal) modal.hidden = true;
  });
  if (targetKey === 'device') openSetupDeviceStep();
  else if (targetKey === 'schedule') openSetupScheduleStep();
}

function openFirstRunSetupModal() {
  const modal = document.getElementById('first-run-setup-modal');
  if (!modal) return;
  renderWizardProgress('wizard-progress-password', 'password');
  document.getElementById('first-run-setup-error').textContent = '';
  document.getElementById('first-run-password').value = '';
  document.getElementById('first-run-password-confirm').value = '';
  modal.hidden = false;
  document.getElementById('first-run-password').focus();
}

async function submitFirstRunSetup() {
  const password = document.getElementById('first-run-password').value;
  const confirm = document.getElementById('first-run-password-confirm').value;
  const result = await api().complete_first_run_setup(password, confirm);
  const error = document.getElementById('first-run-setup-error');
  if (!result.ok) {
    error.textContent = result.message || 'Could not create the administrator password.';
    return;
  }
  document.getElementById('first-run-setup-modal').hidden = true;
  runSetupWizardRouter();
}

// Single router used both at boot and after each wizard step completes -
// asks the backend which step (if any) is still outstanding and shows it,
// or falls through to the normal app state once nothing is left.
async function runSetupWizardRouter() {
  const result = await api().get_setup_wizard_step();
  if (result.step === 'password') { openFirstRunSetupModal(); return; }
  if (result.step === 'device') { openSetupDeviceStep(); return; }
  if (result.step === 'schedule') { openSetupScheduleStep(); return; }
  if (result.step === 'branding') { openSetupBrandingStep(); return; }
  const session = await api().get_session_state();
  currentRole = session.role || 'guest';
  applySessionState(session);
}

function openSetupDeviceStep() {
  const modal = document.getElementById('setup-device-modal');
  if (!modal) return;
  renderWizardProgress('wizard-progress-device', 'device');
  updateSetupDeviceStatus();
  modal.hidden = false;
}

async function setupDeviceConnectClick() {
  await toggleConnect();
  await updateSetupDeviceStatus();
}

async function updateSetupDeviceStatus() {
  const connectBtn = document.getElementById('setup-device-connect-btn');
  const continueBtn = document.getElementById('setup-device-continue-btn');
  const sideCard = document.getElementById('setup-device-side-card');
  const sideDetail = document.getElementById('setup-device-side-detail');
  if (!connectBtn || !continueBtn || !sideCard || !sideDetail) return;
  if (connected) {
    connectBtn.textContent = 'Disconnect';
    connectBtn.className = 'hdr-btn danger';
    continueBtn.textContent = 'Continue';
    const status = await api().get_connection_status();
    const lines = formatDeviceStatusLines(status);
    sideDetail.innerHTML = lines.length
      ? lines.map(escapeHtml).join('<br>')
      : 'Connected, but the device hasn\u2019t reported its metadata yet.';
    sideCard.hidden = false;
  } else {
    connectBtn.textContent = 'Connect';
    connectBtn.className = 'hdr-btn';
    continueBtn.textContent = "Skip \u2014 I'll connect it later";
    sideCard.hidden = true;
  }
}

async function completeSetupDeviceStep() {
  await api().complete_setup_device_step(connected);
  document.getElementById('setup-device-modal').hidden = true;
  runSetupWizardRouter();
}

function updateWindowSizeMode() {
  const width = window.innerWidth;
  const mode = width >= 1200 ? 'wide' : width <= 760 ? 'compact' : 'medium';
  document.body.dataset.windowMode = mode;
}

window.addEventListener('resize', updateWindowSizeMode);
document.addEventListener('DOMContentLoaded', updateWindowSizeMode);

function applySetupWeekdaySelection(selectedDays) {
  const normalized = Array.from(new Set((selectedDays || []).map(Number).filter(value => value >= 0 && value <= 6))).sort((a, b) => a - b);
  document.querySelectorAll('.setup-week-day').forEach(button => {
    const day = Number(button.dataset.weekday);
    const isSelected = normalized.includes(day);
    button.classList.toggle('is-off', isSelected);
    button.setAttribute('aria-pressed', String(isSelected));
  });
}

function attachSetupWeekdayToggles() {
  document.querySelectorAll('.setup-week-day').forEach(button => {
    button.addEventListener('click', () => {
      const day = Number(button.dataset.weekday);
      const existing = Array.from(document.querySelectorAll('.setup-week-day.is-off')).map(item => Number(item.dataset.weekday));
      const next = existing.includes(day)
        ? existing.filter(item => item !== day)
        : [...existing, day].sort((a, b) => a - b);
      applySetupWeekdaySelection(next);
    });
  });
}

function openSetupScheduleStep() {
  const modal = document.getElementById('setup-schedule-modal');
  if (!modal) return;
  renderWizardProgress('wizard-progress-schedule', 'schedule');
  document.getElementById('setup-schedule-error').textContent = '';
  attachSetupWeekdayToggles();
  const selectedDays = Array.from(document.querySelectorAll('.setup-week-day.is-off')).map(item => Number(item.dataset.weekday));
  applySetupWeekdaySelection(selectedDays);
  modal.hidden = false;
}

async function completeSetupScheduleStep() {
  const timeIn = document.getElementById('setup-time-in').value;
  const timeOut = document.getElementById('setup-time-out').value;
  const early = Number(document.getElementById('setup-early-threshold').value || 15);
  const late = Number(document.getElementById('setup-late-threshold').value || 15);
  const absent = Number(document.getElementById('setup-absent-threshold').value || 0);
  const selectedDays = Array.from(document.querySelectorAll('.setup-week-day.is-off')).map(item => Number(item.dataset.weekday));
  const error = document.getElementById('setup-schedule-error');
  if (!timeIn || !timeOut) {
    error.textContent = 'Time in and time out are required.';
    return;
  }
  const result = await api().complete_setup_schedule_step(timeIn, timeOut, early, late, absent, selectedDays);
  if (!result.ok) {
    error.textContent = result.message || 'Could not save the schedule.';
    return;
  }
  document.getElementById('setup-schedule-modal').hidden = true;
  runSetupWizardRouter();
}

function openSetupBrandingStep() {
  const modal = document.getElementById('setup-branding-modal');
  if (!modal) return;
  renderWizardProgress('wizard-progress-branding', 'branding');
  document.getElementById('setup-branding-error').textContent = '';
  modal.hidden = false;
}

async function completeSetupBrandingStep() {
  const schoolName = document.getElementById('setup-school-name').value;
  const themeChoice = document.querySelector('input[name="setup-theme"]:checked');
  const theme = themeChoice ? themeChoice.value : 'dark';
  const result = await api().complete_setup_branding_step(schoolName, theme);
  if (!result.ok) {
    document.getElementById('setup-branding-error').textContent = result.message || 'Could not save.';
    return;
  }
  applyTheme(theme);
  applySchoolName(schoolName);
  document.getElementById('setup-branding-modal').hidden = true;
  runSetupWizardRouter();
}

document.addEventListener('keydown', event => {
  if (event.key === 'Enter' && (event.target.id === 'first-run-password' || event.target.id === 'first-run-password-confirm')) {
    event.preventDefault();
    submitFirstRunSetup();
  }
});

function openRoleAuthModal(role) {
  pendingRole = role;
  const modal = document.getElementById('role-auth-modal');
  const password = document.getElementById('role-auth-password');
  const error = document.getElementById('role-auth-error');
  if (!modal || !password) return;
  error.textContent = '';
  password.value = '';
  password.type = 'password';
  const btn = modal.querySelector('.pw-toggle-btn');
  if (btn) btn.textContent = 'Show';
  modal.hidden = false;
  password.focus();
}

function closeRoleAuthModal() {
  pendingRole = null;
  const modal = document.getElementById('role-auth-modal');
  if (modal) modal.hidden = true;
}

async function submitRoleAuth() {
  if (!pendingRole) return;
  const password = document.getElementById('role-auth-password').value;
  const result = await api().authenticate_role(pendingRole, password);
  if (!result.ok) {
    document.getElementById('role-auth-error').textContent = result.message || 'Authentication failed.';
    paintTitlebarRole(currentRole);
    document.getElementById('titlebar-role').value = currentRole;
    document.getElementById('role-select').value = currentRole;
    return;
  }
  closeRoleAuthModal();
  applySessionState(result);
}

document.addEventListener('keydown', event => {
  if (event.key === 'Enter' && event.target.id === 'role-auth-password') {
    event.preventDefault();
    submitRoleAuth();
  }
});

async function requestRoleChange(role) {
  if (role === 'guest') { await lockSession(); return; }
  if (role === currentRole) return;

  const result = await api().set_current_role(role);
  if (result.requires_password === true) {
    openRoleAuthModal(role);
    return;
  }
  if (result.ok) applySessionState(result);
}

async function lockSession() {
  if (!api()) return;
  const result = await api().lock_session();
  applySessionState(result);
}

function openChangePasswordModal() {
  if (!hasRole('admin')) return;
  const modal = document.getElementById('change-password-modal');
  if (!modal) return;
  document.getElementById('password-change-error').textContent = '';
  document.getElementById('current-admin-password').value = '';
  document.getElementById('new-admin-password').value = '';
  // reset both fields back to hidden + "Show" in case they were left
  // toggled visible from a previous open of this modal
  for (const id of ['current-admin-password', 'new-admin-password']) {
    const input = document.getElementById(id);
    input.type = 'password';
    const btn = modal.querySelector(`button[onclick*="${id}"]`);
    if (btn) btn.textContent = 'Show';
  }
  modal.hidden = false;
  document.getElementById('current-admin-password').focus();
}

function closeChangePasswordModal() {
  const modal = document.getElementById('change-password-modal');
  if (modal) modal.hidden = true;
}

async function changeAdminPassword() {
  if (!hasRole('admin')) return;
  const current = document.getElementById('current-admin-password').value;
  const next = document.getElementById('new-admin-password').value;
  const result = await api().change_admin_password(current, next);
  const error = document.getElementById('password-change-error');
  if (!result.ok) {
    error.textContent = result.message || 'Password change failed.';
    return;
  }
  closeChangePasswordModal();
}

// ── Compact mode ──
let compact = false;
function applyCompact(value) {
  compact = !!value;
  document.getElementById('app').classList.toggle('compact', compact);
  document.getElementById('compact-label').textContent = compact ? 'Normal view' : 'Compact view';
  const settingsToggle = document.getElementById('settings-compact-toggle');
  if (settingsToggle) settingsToggle.classList.toggle('on', compact);
}
function applySchoolName(name) {
  const el = document.getElementById('logo-sub-text');
  if (!el) return;
  el.textContent = (name && name.trim()) ? name.trim() : 'Digital Student Identification System';
}
function toggleCompact() {
  applyCompact(!compact);
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

  const canScan = hasPermission('scan');
  // Dashboard's "last scan" card has its own status line (#scan-meta) that
  // was never touched here before - it only got updated by the scan-result
  // handlers, so it stayed stuck on its hardcoded "Device not connected"
  // placeholder text forever, even after a real successful connection.
  // Skip this while actively scanning/showing a real result, since those
  // handlers own scan-meta's text at that point.
  const scanMeta = document.getElementById('scan-meta');
  if (state === 'disconnected') {
    text.textContent = 'Disconnected';
    connBtn.textContent = 'Connect';
    connBtn.className = 'hdr-btn primary';
    scanBtn.disabled = !canScan;
    scanBtn.textContent = 'SCAN';
    scanBtn.classList.remove('danger');
    sbDot.style.background = 'var(--red)';
    sbConn.textContent = 'Disconnected';
    sbDev.style.display = 'none';
    sbDevSep.style.display = 'none';
    devInfo.style.display = 'none';
    if (scanMeta) scanMeta.textContent = 'Device not connected. Connect a reader to begin scanning.';
  } else if (state === 'connected') {
    text.textContent = 'Connected';
    connBtn.textContent = 'Disconnect';
    connBtn.className = 'hdr-btn danger';
    scanBtn.disabled = !canScan;
    sbDot.style.background = 'var(--green)';
    sbConn.textContent = 'Connected';
    sbDev.style.display = 'flex';
    sbDevSep.style.display = 'block';
    devInfo.style.display = 'block';
    if (scanMeta) scanMeta.textContent = canScan ? 'Ready to scan.' : 'Connected.';
  } else if (state === 'scanning') {
    text.textContent = 'Scanning\u2026';
  }
  updateSerialMeta();
}

async function toggleConnect() {
  if (!api()) return;
  if (connectAttemptInFlight) return; // a discovery pass is already running - don't start a second one on top of it
  if (!connected) {
    connectAttemptInFlight = true;
    setConnectButtonsBusy(true);
    try {
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
        document.getElementById('sb-device').innerHTML = `<span>${escapeHtml(res.port || '?')} \u00b7 ${escapeHtml(res.baud || '?')} baud</span>`;
        smAppend(`--- Serial port ${res.port || '?'} opened at ${res.baud || '?'} baud ---`, 'serial-sys');
      } else {
        setStatus('disconnected');
        alert('Could not connect: ' + res.message);
        showSerialTroubleshooting('connect_failed');
      }
    } finally {
      connectAttemptInFlight = false;
      setConnectButtonsBusy(false);
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

// Disables every "Connect" entry point (top bar + wizard device step) while
// a connection attempt is running, and shows a "Connecting..." label.
// ESP32 discovery probes multiple COM ports in sequence with multi-second
// timeouts each, so a full pass can easily take 10-20+ seconds - without
// this, a first-time user re-clicking "Connect" out of impatience spawns a
// second discovery thread on top of the first, they fight over the same
// serial ports, and NEITHER ever completes. (Confirmed: this exact failure
// mode showed up in real logs - six overlapping connect() calls, zero of
// them ever finishing.)
//
// Deliberately does NOT restore any remembered label when busy=false -
// only setStatus() (called right before this, in every code path above)
// owns the top-bar button's text ("Connect" vs "Disconnect"). An earlier
// version of this function snapshotted and restored the pre-click label
// here, which silently overwrote setStatus()'s correct "Disconnect" label
// back to "Connect" immediately after a successful connection - found by
// tracing the exact order these two calls ran in.
function setConnectButtonsBusy(busy) {
  const topBarBtn = document.getElementById('connect-btn');
  if (topBarBtn) {
    topBarBtn.disabled = busy;
    if (busy) topBarBtn.textContent = 'Connecting\u2026';
  }
  const wizardBtn = document.getElementById('setup-device-connect-btn');
  if (wizardBtn) {
    wizardBtn.disabled = busy;
    if (busy) wizardBtn.textContent = 'Connecting\u2026';
  }
}

async function showSerialTroubleshooting(reason = 'manual') {
  if (!api()) return;
  const result = await api().get_serial_troubleshooting();
  const existing = document.getElementById('serial-troubleshooting-overlay');
  if (existing) existing.remove();
  const overlay = document.createElement('div');
  overlay.id = 'serial-troubleshooting-overlay';
  overlay.className = 'modal-overlay';
  const heading = reason === 'reconnect_exhausted' ? 'Reconnect attempts exhausted' : 'ESP32 Connection Help';
  overlay.innerHTML = `<div class="modal-card troubleshooting-modal"><div class="modal-title">${heading}</div><pre class="troubleshooting-message">${escapeHtml(result.message)}</pre><div class="modal-actions"><button class="hdr-btn" data-troubleshoot-close>Close</button><button class="hdr-btn" data-troubleshoot-refresh>Refresh Ports</button><button class="hdr-btn" data-troubleshoot-device>Open Device Manager</button><button class="hdr-btn primary" data-troubleshoot-driver>Open Driver Help</button></div></div>`;
  overlay.querySelector('[data-troubleshoot-close]').addEventListener('click', () => overlay.remove());
  overlay.querySelector('[data-troubleshoot-refresh]').addEventListener('click', async () => { await refreshPortList(); await showSerialTroubleshooting('manual'); });
  overlay.querySelector('[data-troubleshoot-device]').addEventListener('click', async () => { const response = await api().open_device_manager(); if (!response.ok) alert(response.message); });
  overlay.querySelector('[data-troubleshoot-driver]').addEventListener('click', async () => { const response = await api().open_driver_help(); if (!response.ok) alert(response.message || 'Could not open driver help.'); });
  document.body.appendChild(overlay);
}

async function toggleScan() {
  if (!guardPermission('scan', 'Scanning')) return;
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

function handleConnectionChanged(payload) {
  if (payload.connected) {
    updateBatchRetryAvailability();
    return;
  }
  connected = false;
  scanning = false;
  settlePendingDelete(false);
  if (batchDeletePending) {
    const pendingId = batchDeletePending.id;
    settleBatchDelete({ id: pendingId, kind: 'disconnected' });
    if (batchDeleteResult && !batchDeleteResult.remainingIds.includes(pendingId)) {
      batchDeleteResult.remainingIds.unshift(pendingId);
    }
  }
  updateBatchRetryAvailability();
  if (enrollState && enrollState.step === 'enrolling') {
    enrollState.step = 'failed';
    const status = document.getElementById('em-status');
    if (status) status.textContent = 'The ESP32 disconnected. Enrollment was cancelled.';
    resetEnrollForm();
  }
  if (window._wipeWait) settleWipeWait({ event: 'error', message: 'The ESP32 disconnected.' });
  setStatus('disconnected');
}

function handleSerialError(payload) {
  const message = payload && payload.message ? payload.message : 'Serial communication failed.';
  smAppend(`--- Serial error: ${message} ---`, 'serial-sys');
  if (connected) setStatus('disconnected');
}

function handleDataChanged(payload) {
  if (!payload || payload.reason !== 'restore' || !api()) return;
  Promise.all([loadDashboard(), loadAttendancePage(), loadStudentsPage(), loadReportsPage(), loadSettingsPage()]);
  if (connected) api().request_fingerprint_count();
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
  if (batchRfidEraseModal && payload && payload.method === 'batch_rfid_erase') {
    const status = batchRfidEraseModal.querySelector('#batch-rfid-status');
    const count = batchRfidEraseModal.querySelector('#batch-rfid-count');
    const uid = payload.uid || 'unknown card';
    if (payload.event === 'erased') {
      if (status) {
        status.textContent = `Erased ${payload.count}: ${uid}`;
        status.className = 'rfid-modal-status success';
      }
      if (count) count.textContent = `Cards erased: ${payload.count}`;
    } else if (payload.event === 'skipped') {
      if (status) {
        status.textContent = `Skipped (not this tool / unreadable): ${uid}`;
        status.className = 'rfid-modal-status error';
      }
    } else if (payload.event === 'armed') {
      if (status) {
        status.textContent = `Waiting for the same card: ${uid}`;
        status.className = 'rfid-modal-status active';
      }
    }
    return;
  }
  if (manageRfidModal && payload && payload.method === 'card_write') {
    const status = manageRfidModal.querySelector('#rfid-modal-status');
    if (status) {
      status.textContent = payload.success ? 'Encrypted RFID payload written.' : 'Could not write the encrypted RFID payload.';
      status.className = 'rfid-modal-status ' + (payload.success ? 'success' : 'error');
    }
    if (payload.success) setTimeout(() => closeManageRfidDialog(), 750);
    return;
  }
  if (pendingCardBinding && payload && payload.method === 'card' && payload.uid) {
    bindPendingCardFromScan(payload);
  }

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
  document.getElementById('scan-tag').textContent = isMatch ? (payload.attendance_status || 'Present') : 'UNKNOWN';
  document.getElementById('scan-tag').className = 'scan-status-tag ' + (isMatch ? attendanceBadgeClass(payload.attendance_status) : 'unknown');
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
      `<td><span class="badge ${badgeClass(payload.status)}">${escapeHtml(isMatch ? (payload.status || 'UNKNOWN') : 'UNKNOWN')}</span></td>` +
      `<td><span class="badge ${attendanceBadgeClass(payload.attendance_status)}">${escapeHtml(payload.attendance_status || '\u2014')}</span></td>`;
    tbody.insertBefore(tr, tbody.firstChild);
    loadDashboardStats();
    // The API commits the attendance row before emitting scan_result. Reload
    // the selected evaluation window so its rate and leaderboard stay current.
    loadAttendanceEvaluation();
    attendanceOnScanEvent({
      date: now.toISOString().slice(0, 10),
      time: now.toLocaleTimeString('en-US', { hour12: false }),
      student_no: student.student_no || 'N/A',
      student_name: isMatch ? student.student_name : 'Unregistered',
      grade: student.grade || 'N/A',
      section: student.section || 'N/A',
      confidence: payload.confidence,
      status: isMatch ? (payload.status || 'PRESENT') : 'UNKNOWN',
      match_status: isMatch ? (payload.status || 'UNKNOWN') : 'UNKNOWN',
      attendance_status: isMatch ? payload.attendance_status : 'Unknown',
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
  onPeriodChange(true);
  await loadAttendanceEvaluation();
}

// ── Attendance Evaluation (Day / Week / Month) ──
let evalData = null;
const CATEGORY_META = {
  excellent: { label: 'Excellent', dot: 'var(--green)', range: '90\u2013100%' },
  good: { label: 'Good', dot: 'var(--yellow)', range: '75\u201389%' },
  attention: { label: 'Needs attention', dot: '#FB923C', range: '50\u201374%' },
  low: { label: 'Low attendance', dot: 'var(--red)', range: 'below 50%' },
  // Deliberately NOT on the red/orange severity scale - this means "no
  // eligible school days for this student in this period" (enrolled after
  // the period ended, or the period itself has zero data), not "this
  // student has bad attendance". Neutral gray so it doesn't visually read
  // as a warning next to the real low-attendance rows.
  no_data: { label: 'No data', dot: 'var(--muted)', range: 'not enrolled yet / no data' },
};

function todayStr() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
}

// Switches the single date input between month, week, and day controls.
function onPeriodChange(isInitial) {
  const period = document.getElementById('me-period').value;
  const input = document.getElementById('me-date');
  const wantType = period === 'month' ? 'month' : period === 'week' ? 'week' : 'date';
  if (input.type !== wantType) {
    input.type = wantType;
    input.value = '';
  }
  if (!input.value) {
    const now = new Date();
    input.value = wantType === 'month'
      ? `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
      : wantType === 'week' ? currentIsoWeek(now) : todayStr();
  }
  if (!isInitial) loadAttendanceEvaluation();
}

async function loadAttendanceEvaluation() {
  if (!api()) return;
  const body = document.getElementById('me-body');
  const period = document.getElementById('me-period').value;
  const dateVal = document.getElementById('me-date').value;
  if (!dateVal) return;
  const refDate = period === 'month' ? `${dateVal}-01` : period === 'week' ? isoWeekToMonday(dateVal) : dateVal;
  body.innerHTML = '<div class="modal-status" style="padding:10px 0;">Loading\u2026</div>';
  const report = await api().get_attendance_evaluation(period, refDate);
  if (!report.ok) {
    body.innerHTML = `<div class="me-empty">${escapeHtml(report.message || 'Could not load the report.')}</div>`;
    return;
  }
  evalData = report;
  renderAttendanceEvaluation();
}

function formatEvalRangeLabel(report) {
  const opts = { month: 'short', day: 'numeric', year: 'numeric' };
  const start = new Date(report.start_date + 'T00:00:00');
  const end = new Date(report.end_date + 'T00:00:00');
  if (report.period === 'day') return start.toLocaleDateString('en-US', opts);
  if (report.period === 'month') return start.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  return `Week of ${start.toLocaleDateString('en-US', opts)} \u2013 ${end.toLocaleDateString('en-US', opts)}`;
}

function renderAttendanceEvaluation() {
  if (!evalData) return;
  const body = document.getElementById('me-body');
  const rows = [...evalData.rows];
  const sortBy = document.getElementById('me-sort').value;
  // no_data rows (attendance_rate === null) always sort last, regardless of
  // sort mode - they're not "0%", they're "not applicable", and burying
  // them at the bottom of a rate-sorted list would be misleading (reads as
  // "worst attendance" instead of "no data").
  const byNoDataLast = (a, b) => (a.attendance_rate === null) - (b.attendance_rate === null);
  if (sortBy === 'rate') rows.sort((a, b) => byNoDataLast(a, b) || (b.attendance_rate - a.attendance_rate) || a.student_name.localeCompare(b.student_name));
  else if (sortBy === 'name') rows.sort((a, b) => a.student_name.localeCompare(b.student_name));
  else rows.sort((a, b) => byNoDataLast(a, b) || b.days_present - a.days_present || a.student_name.localeCompare(b.student_name));

  const rangeLabel = formatEvalRangeLabel(evalData);

  if (!rows.length) {
    body.innerHTML = `
      <div class="me-empty me-empty-card">
        <div class="me-empty-icon" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="11" cy="11" r="10.5" fill="var(--logo-bg)" stroke="var(--logo-accent)" stroke-width="1"/>
            <path d="M11 6a5 5 0 0 0-5 5" stroke="var(--logo-accent)" stroke-width="1.4" stroke-linecap="round" fill="none"/>
            <path d="M11 8a3 3 0 0 0-3 3" stroke="var(--logo-accent)" stroke-width="1.4" stroke-linecap="round" fill="none"/>
            <circle cx="11" cy="11" r="1" fill="var(--logo-accent)"/>
            <path d="M14 11a3 3 0 0 1-3 3" stroke="var(--logo-accent)" stroke-width="1.4" stroke-linecap="round" fill="none"/>
            <path d="M16 11a5 5 0 0 1-5 5" stroke="var(--logo-accent)" stroke-width="1.4" stroke-linecap="round" fill="none"/>
            <path d="M11 6a5 5 0 0 1 5 5" stroke="var(--logo-accent)" stroke-width="1.4" stroke-linecap="round" fill="none"/>
          </svg>
        </div>
        <div>
          <div class="me-empty-title">No students enrolled yet</div>
          <div class="me-empty-sub">Add a student and enroll a fingerprint to start tracking attendance.</div>
        </div>
      </div>`;
    return;
  }
  if (evalData.total_days === 0) {
    body.innerHTML = `
      <div class="me-empty me-empty-card">
        <div class="me-empty-icon" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="11" cy="11" r="10.5" fill="var(--logo-bg)" stroke="var(--logo-accent)" stroke-width="1"/>
            <path d="M11 6a5 5 0 0 0-5 5" stroke="var(--logo-accent)" stroke-width="1.4" stroke-linecap="round" fill="none"/>
            <path d="M11 8a3 3 0 0 0-3 3" stroke="var(--logo-accent)" stroke-width="1.4" stroke-linecap="round" fill="none"/>
            <circle cx="11" cy="11" r="1" fill="var(--logo-accent)"/>
            <path d="M14 11a3 3 0 0 1-3 3" stroke="var(--logo-accent)" stroke-width="1.4" stroke-linecap="round" fill="none"/>
            <path d="M16 11a5 5 0 0 1-5 5" stroke="var(--logo-accent)" stroke-width="1.4" stroke-linecap="round" fill="none"/>
            <path d="M11 6a5 5 0 0 1 5 5" stroke="var(--logo-accent)" stroke-width="1.4" stroke-linecap="round" fill="none"/>
          </svg>
        </div>
        <div>
          <div class="me-empty-title">No attendance activity recorded</div>
          <div class="me-empty-sub">Nothing was scanned for ${rangeLabel} yet.</div>
        </div>
      </div>`;
    return;
  }

  const topFive = [...evalData.rows].sort((a, b) => b.days_present - a.days_present).slice(0, 5);
  const leaderboard = topFive.map((r, i) =>
    `<div class="me-lb-card"><div class="me-lb-rank">#${i + 1}</div><div class="me-lb-name">${escapeHtml(r.student_name)}</div><div class="me-lb-days">${r.days_present} day${r.days_present === 1 ? '' : 's'}</div></div>`
  ).join('');

  const legend = Object.entries(CATEGORY_META).map(([key, m]) =>
    `<span><i style="background:${m.dot}"></i>${m.label} \u2014 ${m.range}</span>`
  ).join('');

  const dayColLabel = evalData.period === 'day' ? 'Present' : 'Days Present';
  const absentColLabel = evalData.period === 'day' ? 'Absent' : 'Days Absent';

  const tableRows = rows.map(r => {
    const meta = CATEGORY_META[r.category] || CATEGORY_META.low;
    const hasRate = r.attendance_rate !== null && r.attendance_rate !== undefined;
    const rateCell = hasRate
      ? `<div class="me-rate-cell">
          <div class="me-rate-bar-bg"><div class="me-rate-bar-fill" style="width:${r.attendance_rate}%;background:${meta.dot}"></div></div>
          <span>${r.attendance_rate}%</span>
        </div>`
      : `<div class="me-rate-cell">
          <div class="me-rate-bar-bg"><div class="me-rate-bar-fill" style="width:0%;background:${meta.dot}"></div></div>
          <span style="color:var(--muted);">\u2014</span>
        </div>`;
    return `<tr>
      <td>${escapeHtml(r.student_name)}<div style="font-size:10.5px;color:var(--muted);">${escapeHtml(r.student_no)} \u00b7 Grade ${escapeHtml(r.grade)} \u2014 ${escapeHtml(r.section)}</div></td>
      <td>${hasRate ? r.days_present : '\u2014'}</td>
      <td>${hasRate ? r.days_absent : '\u2014'}</td>
      <td>${rateCell}</td>
      <td><span class="me-cat-badge me-cat-${r.category}">${meta.label}</span></td>
    </tr>`;
  }).join('');

  body.innerHTML = `
    <div style="font-size:11px;color:var(--muted);margin-bottom:2px;">${rangeLabel} \u2014 ${evalData.total_days} school day${evalData.total_days === 1 ? '' : 's'} observed</div>
    <div class="me-leaderboard">${leaderboard}</div>
    <div class="me-legend">${legend}</div>
    <div class="data-table-wrap" style="max-height:280px;">
      <table class="data-table">
        <thead><tr><th>Student</th><th>${dayColLabel}</th><th>${absentColLabel}</th><th>Attendance Rate</th><th>Category</th></tr></thead>
        <tbody>${tableRows}</tbody>
      </table>
    </div>`;
}

async function exportAttendanceEvaluationCsv() {
  const period = document.getElementById('me-period').value;
  const dateVal = document.getElementById('me-date').value;
  if (!dateVal) return;
  const refDate = period === 'month' ? `${dateVal}-01` : dateVal;
  const res = await api().export_attendance_evaluation_csv(period, refDate);
  alert(res.ok ? `Exported to:\n${res.path}` : `Export failed: ${res.message}`);
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
  const panel = document.getElementById('recent-activity-panel');
  if (panel) panel.classList.toggle('empty', rows.length === 0);
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="7"><div class="recent-activity-empty">No attendance activity yet.</div></td></tr>';
    return;
  }
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
    `<td><span class="badge ${badgeClass(r.match_status || r.status)}">${escapeHtml((r.match_status || r.status || 'UNKNOWN').toUpperCase())}</span></td>` +
    `<td><span class="badge ${attendanceBadgeClass(r.attendance_status)}">${escapeHtml(r.attendance_status || '\u2014')}</span></td></tr>`;
}

function badgeClass(status) {
  const s = (status || '').toUpperCase();
  if (s.includes('GOOD') || s === 'PRESENT') return 'present';
  if (s === 'LATE') return 'late';
  return 'absent';
}

function attendanceBadgeClass(status) {
  const value = (status || '').toLowerCase();
  if (value === 'unknown') return 'unknown';
  if (value === 'early') return 'early';
  if (value === 'late') return 'late';
  if (value === 'absent') return 'absent';
  if (value === 'out') return 'out';
  return 'present';
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
      `<td><span class="badge ${badgeClass(r.match_status || r.status)}">${escapeHtml((r.match_status || r.status || 'UNKNOWN').toUpperCase())}</span></td>` +
      `<td><span class="badge ${attendanceBadgeClass(r.attendance_status)}">${escapeHtml(r.attendance_status || '\u2014')}</span></td></tr>`;
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
    `<td><span class="badge ${badgeClass(row.match_status || row.status)}">${escapeHtml((row.match_status || row.status || 'UNKNOWN').toUpperCase())}</span></td>` +
    `<td><span class="badge ${attendanceBadgeClass(row.attendance_status)}">${escapeHtml(row.attendance_status || '\u2014')}</span></td></tr>`);
  const countEl = document.getElementById('att-count');
  countEl.textContent = `${tbody.children.length} records`;
}

function isoWeekToMonday(weekValue) {
  const match = /^(\d{4})-W(\d{2})$/.exec(weekValue || '');
  if (!match) return '';
  const year = Number(match[1]);
  const week = Number(match[2]);
  const jan4 = new Date(Date.UTC(year, 0, 4));
  const monday = new Date(jan4);
  monday.setUTCDate(jan4.getUTCDate() - (jan4.getUTCDay() || 7) + 1 + (week - 1) * 7);
  return `${monday.getUTCFullYear()}-${String(monday.getUTCMonth() + 1).padStart(2, '0')}-${String(monday.getUTCDate()).padStart(2, '0')}`;
}

function currentIsoWeek(date) {
  const thursday = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  thursday.setUTCDate(thursday.getUTCDate() + 4 - (thursday.getUTCDay() || 7));
  const yearStart = new Date(Date.UTC(thursday.getUTCFullYear(), 0, 1));
  const week = Math.ceil((((thursday - yearStart) / 86400000) + 1) / 7);
  return `${thursday.getUTCFullYear()}-W${String(week).padStart(2, '0')}`;
}

function formatWeekRange(weekValue) {
  const monday = isoWeekToMonday(weekValue);
  if (!monday) return 'Choose a week';
  const start = new Date(`${monday}T00:00:00`);
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  const format = date => date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  return `Week of ${format(start)} – ${format(end)}`;
}

function updateExportWeekLabel() {
  const input = document.getElementById('export-week');
  const label = document.getElementById('export-week-label');
  if (input && label) label.textContent = formatWeekRange(input.value);
}

async function exportAttendanceCsv(mode, weekValue = '') {
  if (!guardPermission('export', 'Exporting attendance data')) return;
  if (!api()) return;
  const selected = document.getElementById('att-mode');
  const modeKey = mode || (selected ? (selected.value === 'Recent' ? 'recent' : selected.value === 'Last 30 Days' ? 'last30' : 'today') : 'today');
  const weekStart = modeKey === 'weekly' ? isoWeekToMonday(weekValue) : '';
  if (modeKey === 'weekly' && !weekStart) {
    alert('Choose a calendar week first.');
    return;
  }
  const res = await api().export_attendance_csv(modeKey, modeKey === 'recent' ? attendanceOffset : 0, weekStart);
  alert(res.ok ? `Exported to:\n${res.path}` : `Export failed: ${res.message}`);
}

// ── Students ──
async function loadStudentsPage() {
  if (!api()) return;
  const students = await api().get_students();
  const tbody = document.getElementById('stu-tbody');
  studentNames.clear();
  students.forEach(s => studentNames.set(Number(s.fingerprint_id), s.student_name || `Fingerprint ID ${s.fingerprint_id}`));
  const availableIds = new Set(students.map(s => Number(s.fingerprint_id)));
  selectedStudentIds.forEach(id => { if (!availableIds.has(id)) selectedStudentIds.delete(id); });
  tbody.innerHTML = students.map(s =>
    `<tr onclick="selectStudent(this, ${Number(s.fingerprint_id)})" style="cursor:pointer">` +
    `<td class="select-col"><input type="checkbox" class="student-select" data-fingerprint-id="${Number(s.fingerprint_id)}" ${selectedStudentIds.has(Number(s.fingerprint_id)) ? 'checked' : ''} onchange="toggleStudentSelection(event, ${Number(s.fingerprint_id)})" aria-label="Select ${escapeHtml(s.student_name || `fingerprint ID ${s.fingerprint_id}`)}"></td>` +
    `<td>${escapeHtml(s.fingerprint_id)}</td><td>${escapeHtml(s.student_no)}</td><td>${escapeHtml(s.student_name)}</td>` +
    `<td>Grade ${escapeHtml(s.grade)}</td><td>${escapeHtml(s.section)}</td></tr>`
  ).join('');
  document.getElementById('stu-count').textContent = `${students.length} students`;
  updateStudentSelectionUi(students.length);
  if (students.length) selectStudent(tbody.firstElementChild, students[0].fingerprint_id);
}

function toggleStudentSelection(event, fingerprintId) {
  event.stopPropagation();
  const id = Number(fingerprintId);
  if (event.target.checked) selectedStudentIds.add(id);
  else selectedStudentIds.delete(id);
  updateStudentSelectionUi();
}

function toggleAllStudentSelection(checked) {
  document.querySelectorAll('#stu-tbody .student-select').forEach(input => {
    input.checked = checked;
    const id = Number(input.dataset.fingerprintId);
    if (checked) selectedStudentIds.add(id);
    else selectedStudentIds.delete(id);
  });
  updateStudentSelectionUi();
}

function updateStudentSelectionUi(totalStudents) {
  const count = document.getElementById('stu-selected-count');
  const deleteButton = document.getElementById('stu-delete-selected');
  const selectAll = document.getElementById('stu-select-all');
  if (count) count.textContent = `${selectedStudentIds.size} selected`;
  if (deleteButton) deleteButton.disabled = selectedStudentIds.size === 0 || !!batchDeletePending;
  if (selectAll) {
    selectAll.checked = totalStudents > 0 && selectedStudentIds.size === totalStudents;
    selectAll.indeterminate = selectedStudentIds.size > 0 && selectedStudentIds.size < totalStudents;
  }
}

async function selectStudent(row, fingerprintId) {
  document.querySelectorAll('#stu-tbody tr').forEach(r => r.classList.remove('selected-row'));
  if (row) row.classList.add('selected-row');
  const student = await api().get_student(fingerprintId);
  selectedStudent = student;
  if (!student || !student.fingerprint_id) {
    document.getElementById('det-name').textContent = 'No student selected';
    document.getElementById('det-sno').textContent = '—';
    document.getElementById('det-grade').textContent = '—';
    document.getElementById('det-section').textContent = '—';
    document.getElementById('det-fpid').textContent = '—';
    const cardEl = document.getElementById('det-card-uid');
    if (cardEl) cardEl.textContent = 'Not linked';
    const statusBadge = document.getElementById('student-status-today');
    if (statusBadge) {
      statusBadge.textContent = 'Absent';
      statusBadge.className = 'badge ' + attendanceBadgeClass('Absent');
    }
    updateStudentDetailButtons();
    return;
  }
  document.getElementById('det-name').textContent = student.student_name;
  document.getElementById('det-sno').textContent = student.student_no;
  document.getElementById('det-grade').textContent = `Grade ${student.grade}`;
  document.getElementById('det-section').textContent = student.section;
  document.getElementById('det-fpid').textContent = '#' + student.fingerprint_id;
  const cardUid = student.card_uid || '';
  const cardEl = document.getElementById('det-card-uid');
  if (cardEl) cardEl.textContent = cardUid ? cardUid : 'Not linked';
  const status = student.attendance_status || 'Absent';
  const statusBadge = document.getElementById('student-status-today');
  if (statusBadge) {
    statusBadge.textContent = status;
    statusBadge.className = 'badge ' + attendanceBadgeClass(status);
  }
  updateStudentDetailButtons();
}

function updateStudentDetailButtons() {
  const manageBtn = document.getElementById('manage-rfid-btn');
  if (!manageBtn) return;
  manageBtn.disabled = !selectedStudent || !selectedStudent.fingerprint_id;
}

let pendingCardBinding = null;
let manageRfidModal = null;
let batchRfidEraseModal = null;

async function closeBatchRfidEraseDialog() {
  if (api && api().stop_batch_rfid_erase) {
    await api().stop_batch_rfid_erase();
  }
  if (batchRfidEraseModal) {
    batchRfidEraseModal.remove();
    batchRfidEraseModal = null;
  }
}

function openBatchRfidEraseDialog() {
  if (!hasRole('admin') || !hasPermission('enroll')) {
    return;
  }
  if (!connected) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `<div class="modal-card rfid-modal"><div class="modal-title">Erase RFID card data</div><div class="rfid-modal-status error">Device not connected.</div><div class="modal-actions"><button class="hdr-btn" data-batch-erase-close>Done</button></div></div>`;
    modal.querySelector('[data-batch-erase-close]').onclick = () => modal.remove();
    document.body.appendChild(modal);
    return;
  }
  if (batchRfidEraseModal) return;
  const modal = document.createElement('div');
  modal.className = 'modal-overlay';
  modal.innerHTML = `
    <div class="modal-card rfid-modal batch-rfid-modal">
      <div class="modal-title">Erase RFID card data</div>
      <div class="modal-sub">Tap each card to clear the data inside. UID is not changed.</div>
      <div class="batch-rfid-warning">This will erase hidden card data on every card you tap until you click Done.</div>
      <div class="rfid-progress-panel batch-rfid-panel">
        <div class="rfid-modal-status active" id="batch-rfid-status">Waiting for card\u2026</div>
        <label class="batch-rfid-checkbox"><input type="checkbox" id="batch-rfid-unlink"> <span>Also unlink this UID from a student if it is registered</span></label>
        <div id="batch-rfid-count" class="batch-rfid-count">Cards erased: 0</div>
      </div>
      <div class="modal-actions rfid-modal-actions">
        <button id="batch-rfid-start" class="hdr-btn danger">Start listening</button>
        <button id="batch-rfid-done" class="hdr-btn">Done</button>
      </div>
    </div>
  `;
  const status = modal.querySelector('#batch-rfid-status');
  const start = modal.querySelector('#batch-rfid-start');
  const done = modal.querySelector('#batch-rfid-done');
  const unlink = modal.querySelector('#batch-rfid-unlink');
  const setStatus = (message, tone = 'active') => {
    status.textContent = message;
    status.className = `rfid-modal-status ${tone}`;
  };
  start.onclick = async () => {
    start.disabled = true;
    const result = await api().start_batch_rfid_erase(!!unlink.checked);
    if (!result || !result.ok) {
      start.disabled = false;
      setStatus(result && result.message ? result.message : 'Could not start RFID listening.', 'error');
      return;
    }
    setStatus('Waiting for card…', 'active');
  };
  done.onclick = () => closeBatchRfidEraseDialog();
  modal.addEventListener('click', event => {
    if (event.target === modal) closeBatchRfidEraseDialog();
  });
  batchRfidEraseModal = modal;
  document.body.appendChild(modal);
}

async function closeManageRfidDialog() {
  if (api && api().stop_rfid_register_session) {
    await api().stop_rfid_register_session();
  }
  if (manageRfidModal) {
    manageRfidModal.remove();
    manageRfidModal = null;
  }
  pendingCardBinding = null;
}

function promptCardBinding(mode) {
  if (!selectedStudent || !selectedStudent.fingerprint_id) {
    return;
  }
  if (!connected) {
    return;
  }
  pendingCardBinding = { fingerprintId: Number(selectedStudent.fingerprint_id), mode };
}

function openManageRfidDialog() {
  if (!guardPermission('enroll', 'Managing an RFID card')) return;
  if (!selectedStudent || !selectedStudent.fingerprint_id) return;

  const existingCard = selectedStudent.card_uid || '';
  const modal = document.createElement('div');
  modal.className = 'modal-overlay';
  modal.innerHTML = `
    <div class="modal-card rfid-modal">
      <div class="modal-title">Manage RFID</div>
      <div class="modal-sub">RFID is optional. Fingerprint stays the main ID.</div>
      <div class="rfid-modal-layout">
        <div class="rfid-summary-card">
          <div class="rfid-summary-field"><label>Student name</label><div>${escapeHtml(selectedStudent.student_name || '—')}</div></div>
          <div class="rfid-summary-field"><label>Student LRN</label><div>${escapeHtml(selectedStudent.student_no || '—')}</div></div>
          <div class="rfid-summary-field"><label>Fingerprint ID</label><div>#${escapeHtml(String(selectedStudent.fingerprint_id || '—'))}</div></div>
          <div class="rfid-summary-field"><label>Current card</label><div id="rfid-current-card">${existingCard ? escapeHtml(existingCard) : 'Not linked'}</div></div>
        </div>
        <div class="rfid-progress-panel">
          <div class="rfid-progress-title">Card progress</div>
          <div class="rfid-steps">
            <div class="rfid-step active"><span>1</span><strong>Tap card</strong></div>
            <div class="rfid-step"><span>2</span><strong>Check if claimed</strong></div>
            <div class="rfid-step"><span>3</span><strong>Saved</strong></div>
          </div>
          <div id="rfid-mode-cue" class="rfid-mode-cue" ${existingCard ? '' : 'hidden'}>This student already has a card. Tap a new card to replace it.</div>
          <div id="rfid-modal-status" class="rfid-modal-status">Waiting for card…</div>
        </div>
      </div>
      <div id="rfid-unlink-confirm" class="rfid-unlink-confirm" hidden>
        <div id="rfid-unlink-confirm-text" class="rfid-unlink-confirm-text">Unlink this card from the student? The physical card is not erased.</div>
        <div class="rfid-unlink-confirm-actions">
          <button id="rfid-unlink-confirm-yes" class="hdr-btn danger">Unlink</button>
          <button id="rfid-unlink-confirm-no" class="hdr-btn">Back</button>
        </div>
      </div>
      <div class="modal-actions rfid-modal-actions">
        <button id="rfid-modal-primary" class="hdr-btn primary rfid-modal-primary">${existingCard ? 'Replace RFID' : 'Register RFID'}</button>
        <button id="rfid-modal-unlink" class="hdr-btn danger rfid-modal-danger" ${existingCard ? '' : 'disabled'}>Unlink RFID</button>
        <button class="hdr-btn rfid-modal-cancel" data-rfid-cancel>Cancel</button>
      </div>
    </div>
  `;

  const primary = modal.querySelector('#rfid-modal-primary');
  const unlink = modal.querySelector('#rfid-modal-unlink');
  const status = modal.querySelector('#rfid-modal-status');
  const currentCard = modal.querySelector('#rfid-current-card');
  const modeCue = modal.querySelector('#rfid-mode-cue');

  const setStatus = (msg, tone = '') => {
    status.textContent = msg;
    status.className = 'rfid-modal-status' + (tone ? ` ${tone}` : '');
  };

  const updateCardReadout = () => {
    const uid = selectedStudent && selectedStudent.card_uid ? selectedStudent.card_uid : '';
    const text = uid ? uid : 'Not linked';
    const replaceMode = Boolean(uid);
    if (currentCard) currentCard.textContent = text;
    if (primary) {
      primary.textContent = replaceMode ? 'Replace RFID' : 'Register RFID';
      primary.classList.toggle('replace', replaceMode);
    }
    if (modeCue) {
      modeCue.hidden = !replaceMode;
      if (replaceMode) {
        modeCue.textContent = 'This student already has a card. Tap a new card to replace it.';
      }
    }
    if (unlink) unlink.disabled = !uid;
  };

  const renderUnlinkConfirm = (show = false) => {
    const row = modal.querySelector('#rfid-unlink-confirm');
    if (!row) return;
    row.hidden = !show;
    const confirmText = modal.querySelector('#rfid-unlink-confirm-text');
    if (confirmText) confirmText.textContent = 'Unlink this card from the student? The physical card is not erased.';
  };

  primary.addEventListener('click', async () => {
    if (!selectedStudent || !selectedStudent.fingerprint_id) return;
    if (!connected) {
      setStatus('Device not connected.', 'error');
      return;
    }
    renderUnlinkConfirm(false);
    const result = await api().start_rfid_register_session(Number(selectedStudent.fingerprint_id), selectedStudent.card_uid ? 'replace' : 'register');
    if (!result || !result.ok) {
      setStatus(result && result.message ? result.message : 'Could not start RFID listening.', 'error');
      return;
    }
    pendingCardBinding = { fingerprintId: Number(selectedStudent.fingerprint_id), mode: selectedStudent.card_uid ? 'replace' : 'register' };
    setStatus('Waiting for card…', 'active');
  });

  unlink.addEventListener('click', async () => {
    if (!selectedStudent || !selectedStudent.fingerprint_id) return;
    if (!selectedStudent.card_uid) return;
    renderUnlinkConfirm(true);
    setStatus('Unlink this card from the student? The physical card is not erased.', 'active');
    const confirmButton = modal.querySelector('#rfid-unlink-confirm-yes');
    const backButton = modal.querySelector('#rfid-unlink-confirm-no');
    if (confirmButton) {
      confirmButton.onclick = async () => {
        const result = await api().clear_student_card(selectedStudent.fingerprint_id);
        if (!result.ok) {
          renderUnlinkConfirm(false);
          setStatus(result.message || 'Could not unlink the card.', 'error');
          return;
        }
        selectedStudent.card_uid = '';
        updateCardReadout();
        renderUnlinkConfirm(false);
        setStatus('Card unlinked.', 'success');
        await loadStudentsPage();
        setTimeout(() => closeManageRfidDialog(), 750);
      };
    }
    if (backButton) {
      backButton.onclick = () => {
        renderUnlinkConfirm(false);
        setStatus('Waiting for card…', 'active');
      };
    }
  });

  modal.querySelector('[data-rfid-cancel]').addEventListener('click', () => {
    closeManageRfidDialog();
  });
  modal.addEventListener('click', event => {
    if (event.target === modal) closeManageRfidDialog();
  });

  manageRfidModal = modal;
  document.body.appendChild(modal);
  updateCardReadout();
}

function registerSelectedStudentCard() {
  if (!guardPermission('enroll', 'Registering an RFID card')) return;
  openManageRfidDialog();
}

function replaceSelectedStudentCard() {
  if (!guardPermission('enroll', 'Replacing an RFID card')) return;
  openManageRfidDialog();
}

function unlinkSelectedStudentCard() {
  if (!guardPermission('enroll', 'Unlinking an RFID card')) return;
  openManageRfidDialog();
}

async function bindPendingCardFromScan(payload) {
  if (!pendingCardBinding || !payload || !payload.uid) return false;
  const binding = pendingCardBinding;
  pendingCardBinding = null;

  if (binding.mode === 'unlink') {
    return false;
  }

  const result = await api().bind_student_card(binding.fingerprintId, payload.uid);
  const message = result && result.message ? result.message : 'RFID registration updated.';

  if (manageRfidModal) {
    const status = manageRfidModal.querySelector('#rfid-modal-status');
    const currentCard = manageRfidModal.querySelector('#rfid-current-card');
    if (/already registered/i.test(message)) {
      const studentName = selectedStudent && selectedStudent.student_name ? selectedStudent.student_name : 'another student';
      const lrn = selectedStudent && selectedStudent.student_no ? ` (LRN ${selectedStudent.student_no})` : '';
      if (status) {
        status.textContent = `This card is already registered to ${studentName}${lrn}.`;
        status.className = 'rfid-modal-status error';
      }
      if (currentCard) currentCard.textContent = selectedStudent && selectedStudent.card_uid ? selectedStudent.card_uid : 'Not linked';
    } else if (result && result.ok) {
      if (selectedStudent) selectedStudent.card_uid = payload.uid;
      if (currentCard) currentCard.textContent = payload.uid;
      if (manageRfidModal) {
        const primary = manageRfidModal.querySelector('#rfid-modal-primary');
        if (primary) {
          primary.textContent = 'Replace RFID';
          primary.classList.add('replace');
        }
        const modeCue = manageRfidModal.querySelector('#rfid-mode-cue');
        if (modeCue) {
          modeCue.hidden = false;
          modeCue.textContent = 'This student already has a card. Tap a new card to replace it.';
        }
        const unlink = manageRfidModal.querySelector('#rfid-modal-unlink');
        if (unlink) unlink.disabled = false;
      }
      if (status) {
        status.textContent = `Card claimed: ${payload.uid}. Tap the same card again to write encrypted data.`;
        status.className = 'rfid-modal-status success';
      }
    } else {
      if (status) {
        status.textContent = message || 'Could not register the card.';
        status.className = 'rfid-modal-status error';
      }
    }
  }

  await loadStudentsPage();
  updateStudentDetailButtons();
  return true;
}

let pendingDelete = null; // { fingerprintId, resolve }

function showDestructiveConfirm(title, message, confirmLabel) {
  return new Promise(resolve => {
    const existing = document.getElementById('destructive-confirm-overlay');
    if (existing) existing.remove();
    const overlay = document.createElement('div');
    overlay.id = 'destructive-confirm-overlay';
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal-card confirm-modal">
        <div class="modal-title">${escapeHtml(title)}</div>
        <div class="modal-sub">${escapeHtml(message)}</div>
        <div class="confirm-warning">This action cannot be undone.</div>
        <div class="modal-actions">
          <button class="hdr-btn" data-confirm-cancel>Cancel</button>
          <button class="hdr-btn danger" data-confirm-ok>${escapeHtml(confirmLabel)}</button>
        </div>
      </div>`;
    const finish = value => {
      overlay.remove();
      resolve(value);
    };
    overlay.querySelector('[data-confirm-cancel]').addEventListener('click', () => finish(false));
    overlay.querySelector('[data-confirm-ok]').addEventListener('click', () => finish(true));
    overlay.addEventListener('click', event => {
      if (event.target === overlay) finish(false);
    });
    document.body.appendChild(overlay);
    overlay.querySelector('[data-confirm-cancel]').focus();
  });
}

async function deleteSelectedStudent() {
  if (!guardPermission('delete', 'Deleting a student')) return;
  if (!selectedStudent || !selectedStudent.fingerprint_id) return;
  const fpid = selectedStudent.fingerprint_id;
  const name = selectedStudent.student_name;

  if (!connected) {
    alert('Connect to the ESP32 first.');
    return;
  }
  const confirmed = await showDestructiveConfirm(
    'Confirm Delete Student',
    `Delete ${name}? The student record and fingerprint ID ${fpid} will be removed. Attendance history will be preserved as unregistered.`,
    'Confirm Delete'
  );
  if (!confirmed) return;

  const deleteWait = waitForDelete(fpid);
  const res = await api().delete_on_device(fpid);
  if (!res.ok) {
    settlePendingDelete(false);
    alert('Could not delete: ' + res.message);
    return;
  }

  const deleted = await deleteWait;
  if (deleted) await loadStudentsPage();
}

async function deleteSelectedStudents() {
  if (!guardPermission('delete', 'Deleting students')) return;
  const ids = Array.from(selectedStudentIds);
  if (!ids.length) return;
  if (!connected) {
    alert('Connect to the ESP32 first.');
    return;
  }
  const confirmed = await showDestructiveConfirm(
    'Confirm Delete Students',
    `Delete ${ids.length} selected student${ids.length === 1 ? '' : 's'}? Each fingerprint will be removed from the connected device before its local student record is deleted.`,
    'Confirm Delete'
  );
  if (!confirmed) return;
  batchDeleteResult = {
    results: [],
    remainingIds: ids.slice(),
    labels: Object.fromEntries(ids.map(id => [id, studentNames.get(id) || `Fingerprint ID ${id}`])),
    interrupted: false,
  };
  await processBatchDelete();
}

async function processBatchDelete() {
  if (!batchDeleteResult || batchDeletePending) return;
  if (!guardPermission('delete', 'Deleting students')) return;
  batchDeletePending = true;
  updateStudentSelectionUi();
  while (batchDeleteResult.remainingIds.length) {
    if (!connected) {
      batchDeleteResult.interrupted = true;
      break;
    }
    const fingerprintId = batchDeleteResult.remainingIds.shift();
    const result = await deleteOneForBatch(fingerprintId);
    if (result.kind === 'disconnected') {
      batchDeleteResult.interrupted = true;
      break;
    }
    batchDeleteResult.results.push(result);
  }
  batchDeletePending = false;
  updateStudentSelectionUi();
  await loadStudentsPage();
  showBatchDeleteResults();
}

function deleteOneForBatch(fingerprintId) {
  return new Promise(async resolve => {
    if (!connected) {
      resolve({ id: fingerprintId, kind: 'disconnected' });
      return;
    }
    const wait = waitForBatchDelete(fingerprintId, resolve);
    try {
      const response = await api().delete_on_device(fingerprintId);
      if (!response.ok) {
        const disconnected = !connected || /disconnect|connect to the ESP32/i.test(response.message || '');
        if (disconnected && batchDeleteResult && !batchDeleteResult.remainingIds.includes(fingerprintId)) {
          batchDeleteResult.remainingIds.unshift(fingerprintId);
        }
        settleBatchDelete({ id: fingerprintId, kind: disconnected ? 'disconnected' : 'send_failed', message: response.message });
      }
    } catch (error) {
      const disconnected = !connected;
      if (disconnected && batchDeleteResult && !batchDeleteResult.remainingIds.includes(fingerprintId)) {
        batchDeleteResult.remainingIds.unshift(fingerprintId);
      }
      settleBatchDelete({ id: fingerprintId, kind: disconnected ? 'disconnected' : 'send_failed', message: error && error.message });
    }
    await wait;
  });
}

function waitForBatchDelete(fingerprintId, resolve, timeoutMs = 15000) {
  const timer = setTimeout(() => {
    if (batchDeletePending && batchDeletePending.id === fingerprintId) {
      batchDeletePending = null;
      resolve({ id: fingerprintId, kind: 'timeout' });
    }
  }, timeoutMs);
  batchDeletePending = { id: fingerprintId, resolve: result => { clearTimeout(timer); resolve(result); } };
}

function settleBatchDelete(result) {
  if (!batchDeletePending) return;
  const pending = batchDeletePending;
  batchDeletePending = null;
  pending.resolve(result);
}

async function handleBatchDeleteProgress(payload) {
  if (!batchDeletePending || payload.id !== batchDeletePending.id) return;
  const id = batchDeletePending.id;
  if (payload.event === 'success') {
    try {
      const response = await api().delete_student(id);
      settleBatchDelete({ id, kind: response && response.ok ? 'deleted' : 'database_failed', message: response && response.message });
    } catch (error) {
      settleBatchDelete({ id, kind: 'database_failed', message: error && error.message });
    }
  } else if (payload.event === 'error') {
    settleBatchDelete({ id, kind: 'device_failed' });
  }
}

function showBatchDeleteResults(completed = batchDeleteResult) {
  if (!completed) return;
  const existing = document.getElementById('batch-delete-results-overlay');
  if (existing) existing.remove();
  const overlay = document.createElement('div');
  overlay.id = 'batch-delete-results-overlay';
  overlay.className = 'modal-overlay';
  const rows = completed.results.map(result => {
    const label = completed.labels[result.id] || studentNames.get(result.id) || `Fingerprint ID ${result.id}`;
    const text = {
      deleted: 'Deleted',
      device_failed: 'Device failed; database unchanged',
      timeout: 'Timed out; database unchanged',
      send_failed: 'Command failed; database unchanged',
      database_failed: 'Device deleted; database update failed',
    }[result.kind] || result.kind;
    return `<li><strong>${escapeHtml(label)}</strong> (ID ${result.id}): ${escapeHtml(text)}</li>`;
  }).join('');
  const remaining = completed.remainingIds.map(id => `<li><strong>${escapeHtml(completed.labels[id] || studentNames.get(id) || `Fingerprint ID ${id}`)}</strong> (ID ${id}): Waiting for retry</li>`).join('');
  overlay.innerHTML = `<div class="modal-card batch-results-modal"><div class="modal-title">Delete Results</div><div class="modal-sub">${completed.interrupted ? 'The device disconnected. Successful deletions were kept; remaining students were not changed.' : 'Deletion completed.'}</div><ul class="batch-result-list">${rows}${remaining}</ul><div class="modal-actions"><button class="hdr-btn" data-results-close>Close</button>${completed.remainingIds.length ? '<button class="hdr-btn danger" data-results-retry disabled>Retry remaining</button>' : ''}</div></div>`;
  overlay.querySelector('[data-results-close]').addEventListener('click', () => { overlay.remove(); if (!completed.remainingIds.length) batchDeleteResult = null; });
  const retry = overlay.querySelector('[data-results-retry]');
  if (retry) retry.addEventListener('click', async () => {
    if (!guardPermission('delete', 'Deleting students')) return;
    overlay.remove();
    batchDeleteResult = completed;
    batchDeleteResult.interrupted = false;
    await processBatchDelete();
  });
  document.body.appendChild(overlay);
  updateBatchRetryAvailability();
}

function updateBatchRetryAvailability() {
  const retry = document.querySelector('[data-results-retry]');
  if (retry) retry.disabled = !connected || !!batchDeletePending;
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

function settlePendingDelete(value) {
  if (!pendingDelete) return;
  const pending = pendingDelete;
  pendingDelete = null;
  pending.resolve(value);
}

function handleDeleteProgress(payload) {
  if (batchDeletePending) {
    handleBatchDeleteProgress(payload);
    return;
  }
  if (!pendingDelete || payload.id !== pendingDelete.fingerprintId) return;
  if (payload.event === 'success') {
    const operation = pendingDelete;
    api().delete_student(operation.fingerprintId).then(result => {
      if (!result || !result.ok) {
        alert(`The device deleted fingerprint ID ${operation.fingerprintId}, but the database could not be updated: ${result && result.message ? result.message : 'unknown error'}.`);
      }
      if (pendingDelete === operation) {
        pendingDelete = null;
        operation.resolve(!!(result && result.ok));
      }
    }).catch(error => {
      if (pendingDelete === operation) {
        pendingDelete = null;
        operation.resolve(false);
      }
      alert(`The device was updated, but the database operation failed: ${error && error.message ? error.message : 'unknown error'}.`);
    });
  } else if (payload.event === 'error') {
    const operation = pendingDelete;
    alert(`The device reported it could not delete fingerprint ID ${operation.fingerprintId}. Nothing was removed from the database.`);
    pendingDelete = null;
    operation.resolve(false);
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
      <div class="modal-field"><label>Student LRN</label><input id="edit-sno" type="text" value="${escapeHtml(s.student_no)}"></div>
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
  if (!guardPermission('wipe', 'Wiping metadata')) return;
  if (!connected) { alert('Connect to the ESP32 first.'); return; }
  const confirmed = await showDestructiveConfirm(
    'Confirm Wipe Metadata',
    'Remove all stored identification metadata from the connected ESP32 and clear the linked student and attendance data.',
    'Confirm Wipe Metadata'
  );
  if (!confirmed) return;
  const wipeWait = waitForWipe();
  const res = await api().wipe_all_on_device();
  if (!res.ok) {
    settleWipeWait({ event: 'error', message: res.message });
    alert(res.message);
    return;
  }
  const status = document.getElementById('em-status');
  if (status) status.textContent = res.message;
  const event = await wipeWait;
  if (event.event === 'timeout') {
    alert('Timed out waiting for the device to finish wiping metadata.');
  } else if (event.event === 'error') {
    alert(event.message || 'The device could not wipe metadata.');
  } else if (event.event === 'success') {
    await Promise.all([loadDashboard(), loadAttendancePage(), loadStudentsPage(), loadReportsPage()]);
    selectedStudent = null;
    alert(`All metadata and linked local data were cleared. Removed ${event.students || 0} student record(s) and ${event.attendance || 0} attendance record(s).`);
  }
}

async function wipeAllData() {
  if (!guardPermission('wipe', 'Wiping local data')) return;
  if (!confirm('Wipe all students and attendance data from the database? Device fingerprints will not be changed.')) return;
  const res = await api().wipe_all_data();
  if (!res.ok) {
    alert(res.message || 'Could not wipe local database data.');
    return;
  }
  selectedStudent = null;
  await Promise.all([loadDashboard(), loadAttendancePage(), loadStudentsPage(), loadReportsPage()]);
  alert(res.message);
}

function waitForWipe(timeoutMs = 15000) {
  return new Promise(resolve => {
    const timer = setTimeout(() => {
      if (window._wipeWait) {
        window._wipeWait = null;
        resolve({ event: 'timeout' });
      }
    }, timeoutMs);
    window._wipeWait = event => {
      clearTimeout(timer);
      window._wipeWait = null;
      resolve(event);
    };
  });
}

function settleWipeWait(event) {
  if (window._wipeWait) window._wipeWait(event);
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
  if (!connected) {
    alert('Connect to the ESP32 first.');
    return;
  }
  openEnrollDialog(selectedStudent);
}

function openEnrollDialog(existing) {
  if (!guardPermission('enroll', 'Student enrollment')) return;
  closeEnrollDialog();
  const overlay = document.createElement('div');
  overlay.id = 'enroll-modal-overlay';
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="modal-card">
      <div class="modal-title">${existing ? 'Re-enroll Student' : 'Enroll Student'}</div>
      <div class="modal-sub">${existing ? 'A new fingerprint slot will be assigned by the device.' : 'The device assigns the fingerprint ID automatically \u2014 fill in the student first, then scan. RFID is optional. Register it later from Student Details.'}</div>
      <div class="enroll-layout">
        <div class="enroll-form">
          <div class="modal-field"><label>Student LRN</label><input id="em-sno" type="text" value="${existing ? escapeHtml(existing.student_no) : ''}"><div class="field-feedback" id="em-sno-feedback"></div></div>
          <div class="modal-field"><label>Student Name</label><input id="em-name" type="text" placeholder="Last, First M." value="${existing ? escapeHtml(existing.student_name) : ''}"><div class="field-feedback" id="em-name-feedback"></div></div>
          <div class="modal-field-row">
            <div class="modal-field"><label>Grade</label><input id="em-grade" type="text" value="${existing ? escapeHtml(existing.grade) : ''}"><div class="field-feedback" id="em-grade-feedback"></div></div>
            <div class="modal-field"><label>Section</label><input id="em-section" type="text" value="${existing ? escapeHtml(existing.section) : ''}"><div class="field-feedback" id="em-section-feedback"></div></div>
          </div>
          <div class="validation-summary" id="em-validation-summary"></div>
          <div class="modal-status" id="em-status">${connected ? '' : 'Connect to the ESP32 first.'}</div>
          <div class="modal-id" id="em-id" style="display:none;"></div>
        </div>
        <div class="enroll-progress-panel">
          <div class="enroll-progress-title">Sensor progress</div>
          <div class="enroll-steps" id="em-steps">
            <div class="enroll-step" data-step="1"><span>1</span><strong>Place finger</strong><small>First scan</small></div>
            <div class="enroll-step" data-step="2"><span>2</span><strong>Remove finger</strong><small>Wait for prompt</small></div>
            <div class="enroll-step" data-step="3"><span>3</span><strong>Scan same finger</strong><small>Second scan</small></div>
            <div class="enroll-step" data-step="4"><span>4</span><strong>Saved</strong><small>Ready to register</small></div>
          </div>
          <div class="enroll-log" id="em-log" aria-live="polite"><div class="enroll-log-line muted">Waiting to enroll student.</div></div>
        </div>
      </div>
      <div class="modal-actions">
        <button class="hdr-btn" onclick="closeEnrollDialog()">Cancel</button>
        <button class="hdr-btn primary" id="em-primary-btn" onclick="enrollPrimaryAction()" ${connected ? '' : 'disabled'}>Enroll Student</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);
  enrollState = { existing: existing || null, assignedId: null, step: 'initial' };
  ['em-sno', 'em-name', 'em-grade', 'em-section'].forEach(id => {
    document.getElementById(id).addEventListener('input', validateEnrollmentFields);
  });
  validateEnrollmentFields();
}

let enrollmentValidationSequence = 0;

async function validateEnrollmentFields() {
  if (!enrollState || enrollState.step !== 'initial' || !api()) return false;
  const sequence = ++enrollmentValidationSequence;
  const values = {
    student_no: document.getElementById('em-sno').value,
    student_name: document.getElementById('em-name').value,
    grade: document.getElementById('em-grade').value,
    section: document.getElementById('em-section').value,
  };
  try {
    const result = await api().validate_student_fields(
      values.student_no, values.student_name, values.grade, values.section
    );
    if (sequence !== enrollmentValidationSequence || !enrollState) return false;
    const mapping = {
      student_no: 'sno',
      student_name: 'name',
      grade: 'grade',
      section: 'section',
    };
    let firstInvalid = null;
    Object.entries(mapping).forEach(([field, suffix]) => {
      const input = document.getElementById(`em-${suffix}`);
      const feedback = document.getElementById(`em-${suffix}-feedback`);
      const item = result.fields[field];
      if (!input || !feedback || !item) return;
      const valid = !!item.valid;
      input.classList.toggle('field-valid', valid);
      input.classList.toggle('field-invalid', !valid);
      feedback.className = `field-feedback ${valid ? 'valid' : 'invalid'}`;
      feedback.textContent = valid ? 'Valid' : item.message;
      if (!valid && !firstInvalid) firstInvalid = item.message;
    });
    const summary = document.getElementById('em-validation-summary');
    if (summary) {
      summary.className = `validation-summary ${result.all_valid ? 'valid' : 'invalid'}`;
      summary.textContent = result.all_valid ? 'Student information is valid' : firstInvalid || 'Please correct the highlighted fields.';
    }
    const button = document.getElementById('em-primary-btn');
    if (button) button.disabled = !result.all_valid || !connected;
    return !!result.all_valid;
  } catch (error) {
    if (sequence === enrollmentValidationSequence) {
      const summary = document.getElementById('em-validation-summary');
      if (summary) {
        summary.className = 'validation-summary invalid';
        summary.textContent = 'Validation is unavailable. Please try again.';
      }
      const button = document.getElementById('em-primary-btn');
      if (button) button.disabled = true;
    }
    return false;
  }
}

function closeEnrollDialog() {
  const overlay = document.getElementById('enroll-modal-overlay');
  if (overlay) overlay.remove();
  if (enrollState && enrollState.step === 'enrolling' && api()) {
    api().cancel_enroll();
  } else if (enrollState && enrollState.assignedId && !enrollState.saved && api()) {
    api().discard_enrollment(enrollState.assignedId);
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
  if (!(await validateEnrollmentFields())) {
    document.getElementById('em-status').textContent = 'Please fill in all student fields with valid data.';
    return;
  }
  enrollState.form = { sno, name, grade, section };

  const btn = document.getElementById('em-primary-btn');
  btn.disabled = true;
  btn.textContent = 'Enrolling\u2026';
  ['em-sno', 'em-name', 'em-grade', 'em-section'].forEach(id => document.getElementById(id).disabled = true);

  enrollState.step = 'enrolling';
  const res = await api().start_enroll();
  document.getElementById('em-status').textContent = res.message;
  if (!res.ok) {
    enrollState.step = 'initial';
    btn.disabled = false;
    btn.textContent = 'Enroll Student';
    ['em-sno', 'em-name', 'em-grade', 'em-section'].forEach(id => document.getElementById(id).disabled = false);
    return;
  }
}

function handleEnrollProgress(payload) {
  if (!enrollState || enrollState.step === 'initial') return;
  const status = document.getElementById('em-status');
  const idLabel = document.getElementById('em-id');
  const btn = document.getElementById('em-primary-btn');
  if (!status || !btn) return;

  const log = document.getElementById('em-log');
  const appendLog = (message, kind = '') => {
    if (!log || !message) return;
    const line = document.createElement('div');
    line.className = `enroll-log-line ${kind}`.trim();
    line.textContent = message;
    log.appendChild(line);
    log.scrollTop = log.scrollHeight;
  };
  const setProgress = (activeStep, completedThrough = activeStep - 1, state = 'active') => {
    document.querySelectorAll('#em-steps .enroll-step').forEach(step => {
      const number = Number(step.dataset.step);
      step.classList.toggle('active', number === activeStep && state === 'active');
      step.classList.toggle('complete', number <= completedThrough || state === 'success' && number <= 4);
      step.classList.toggle('error', state === 'error' && number === activeStep);
    });
  };

  if (payload.event === 'enrolling') {
    status.textContent = `Enrolling as ID #${payload.id}\u2026 follow the prompts on the sensor.`;
    if (log) log.replaceChildren();
    appendLog(`Enrolling finger as ID #${payload.id}`, 'active');
    setProgress(1, 0);
  } else if (payload.event === 'step') {
    appendLog(payload.message, 'active');
    const message = (payload.message || '').toLowerCase();
    if (message.includes('step 2') || message.includes('remove finger') || message.includes('finger removed')) setProgress(2, 1);
    else if (message.includes('step 3') || message.includes('same finger')) setProgress(3, 2);
    else if (message.includes('image taken') || message.includes('image converted')) setProgress(message.includes('converted') ? 1 : 1, 0);
  } else if (payload.event === 'success') {
    enrollState.assignedId = parseInt(payload.id, 10);
    enrollState.step = 'success';
    status.textContent = 'Student enrollment saved on the device.';
    appendLog(`Success! Finger saved as ID #${payload.id}`, 'success');
    setProgress(4, 3, 'success');
    idLabel.style.display = 'block';
    idLabel.textContent = `Assigned ID: #${payload.id}`;
    btn.disabled = false;
    btn.textContent = 'Save Student';
  } else if (payload.event === 'cancelled') {
    status.textContent = 'Enrollment was cancelled on the device.';
    appendLog('Enrollment cancelled.', 'error');
    setProgress(1, 0, 'error');
    resetEnrollForm();
  } else if (payload.event === 'error') {
    status.textContent = 'The device reported an enrollment error.';
    appendLog('Enrollment failed. Check the sensor and try again.', 'error');
    setProgress(1, 0, 'error');
    resetEnrollForm();
  }
}

function resetEnrollForm() {
  const btn = document.getElementById('em-primary-btn');
  if (!btn) return;
  btn.disabled = false;
  btn.textContent = 'Enroll Student';
  ['em-sno', 'em-name', 'em-grade', 'em-section'].forEach(id => document.getElementById(id).disabled = false);
  if (enrollState) enrollState.step = 'initial';
}

async function saveEnrolledStudent() {
  if (!enrollState || !enrollState.assignedId || !enrollState.form) return;
  const { sno, name, grade, section } = enrollState.form;
  const newId = enrollState.assignedId;
  const previous = enrollState.existing;

  // Re-enroll: the device assigned a new slot, so retire the old one instead
  // of leaving a stale duplicate row (and a stale template still on the
  // sensor for that old ID).
  if (previous && previous.fingerprint_id && previous.fingerprint_id !== newId) {
    const deleteWait = waitForDelete(previous.fingerprint_id);
    const del = await api().delete_on_device(previous.fingerprint_id);
    if (!del.ok) {
      settlePendingDelete(false);
      document.getElementById('em-status').textContent = `Saved new fingerprint, but the old device record could not be removed: ${del.message}`;
      return;
    }
    const deleted = await deleteWait;
    if (!deleted) {
      document.getElementById('em-status').textContent = 'New fingerprint saved, but the old fingerprint remains on the device. Review the student records before continuing.';
      return;
    }
  }

  const res = await api().save_student(newId, sno, name, grade, section, previous && previous.fingerprint_id ? previous.fingerprint_id : 0);
  if (!res.ok) {
    document.getElementById('em-status').textContent = 'Could not save student: ' + res.message;
    return;
  }

  enrollState.saved = true;

  closeEnrollDialog();
  await loadStudentsPage();
  api().request_fingerprint_count();
}

async function exportStudentsCsv() {
  if (!guardPermission('export', 'Exporting students data')) return;
  const res = await api().export_students_csv();
  alert(res.ok ? `Exported to:\n${res.path}` : `Export failed: ${res.message}`);
}

// ── Reports ──
async function loadReportsPage() {
  if (!api()) return;
  const exportWeek = document.getElementById('export-week');
  if (exportWeek && !exportWeek.value) {
    exportWeek.value = currentIsoWeek(new Date());
    updateExportWeekLabel();
  }
  await generateStatsReport();
  await loadBackupsList();
  const stats = await api().get_dashboard_stats();
  document.getElementById('rpt-today-count').textContent = `${stats.scans_today} scans`;
  document.getElementById('rpt-students-count').textContent = `${stats.total_students} records`;
  document.getElementById('rpt-last30-label').textContent = new Date().toLocaleString('en-US', { month: 'long', year: 'numeric' });
}

async function exportStatisticsReport() {
  if (!guardPermission('export', 'Exporting reports')) return;
  const result = await api().export_statistics_report();
  alert(result.ok ? `Exported to:\n${result.path}` : `Export failed: ${result.message}`);
}

async function showStatisticsCharts() {
  if (!guardPermission('export', 'Viewing charts')) return;
  const overlay = document.createElement('div');
  overlay.id = 'statistics-charts-overlay';
  overlay.className = 'modal-overlay';
  overlay.innerHTML = '<div class="modal-card chart-modal"><div class="modal-title">Attendance Analytics Charts</div><div class="chart-tabs" role="tablist"><button class="chart-tab active" data-chart-tab="timeline">Timeline</button><button class="chart-tab" data-chart-tab="section">By Section</button><button class="chart-tab" data-chart-tab="grade">By Grade</button></div><div class="chart-content" id="chart-content"><div class="chart-loading">Loading chart data...</div></div><div class="modal-actions"><button class="hdr-btn" data-chart-close>Close</button></div></div>';
  document.body.appendChild(overlay);
  overlay.querySelector('[data-chart-close]').addEventListener('click', () => overlay.remove());
  overlay.addEventListener('click', event => { if (event.target === overlay) overlay.remove(); });
  overlay.querySelectorAll('[data-chart-tab]').forEach(tab => tab.addEventListener('click', () => {
    overlay.querySelectorAll('[data-chart-tab]').forEach(item => item.classList.toggle('active', item === tab));
    renderStatisticsChartTab(overlay, tab.dataset.chartTab);
  }));
  try {
    const report = await api().get_statistics_report();
    if (!report || report.ok === false) throw new Error(report && report.message ? report.message : 'Charts are unavailable.');
    overlay._chartReport = report;
    renderStatisticsChartTab(overlay, 'timeline');
  } catch (error) {
    overlay.querySelector('#chart-content').innerHTML = `<div class="chart-state error">${escapeHtml(error && error.message ? error.message : 'Unable to load charts. Please check the application log.')}</div>`;
  }
}

function chartEmpty(message) {
  return `<div class="chart-state">${escapeHtml(message)}</div>`;
}

function renderStatisticsChartTab(overlay, tab) {
  const report = overlay._chartReport;
  const content = overlay.querySelector('#chart-content');
  if (!report) return;
  if (tab === 'timeline') {
    content.innerHTML = renderAttendanceTimeline(report.attendance_timeline || []);
  } else if (tab === 'section') {
    content.innerHTML = renderSectionChart(report.students_by_section || []);
  } else {
    content.innerHTML = renderAttendanceGradeChart(report.attendance_by_grade || []);
  }
}

function renderAttendanceTimeline(rows) {
  if (!rows.length) return chartEmpty('No attendance records are available for the timeline.');
  const width = 900, height = 360, left = 58, right = 24, top = 24, bottom = 58;
  const max = Math.max(...rows.map(row => Number(row.count) || 0), 1);
  const x = index => left + (rows.length === 1 ? (width - left - right) / 2 : index * (width - left - right) / (rows.length - 1));
  const y = value => height - bottom - (value / max) * (height - top - bottom);
  const points = rows.map((row, index) => `${x(index)},${y(Number(row.count) || 0)}`).join(' ');
  const area = `${left},${height - bottom} ${points} ${x(rows.length - 1)},${height - bottom}`;
  const labels = rows.map((row, index) => `<text x="${x(index)}" y="${height - 28}" text-anchor="middle" class="chart-axis-label">${escapeHtml(row.date.slice(5))}</text>`).join('');
  const dots = rows.map((row, index) => `<circle cx="${x(index)}" cy="${y(Number(row.count) || 0)}" r="4" class="chart-point"><title>${escapeHtml(row.date)}: ${escapeHtml(row.count)} scans</title></circle>`).join('');
  return `<div class="chart-title">Attendance Timeline (Last 30 Dates)</div><svg class="chart-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Attendance timeline"><line x1="${left}" y1="${height - bottom}" x2="${width - right}" y2="${height - bottom}" class="chart-axis"/><polygon points="${area}" class="chart-area"/><polyline points="${points}" class="chart-line"/>${dots}${labels}<text x="14" y="${top + 8}" class="chart-axis-label">${max}</text><text x="${left}" y="${height - 8}" class="chart-axis-label">Date</text></svg>`;
}

function renderSectionChart(rows) {
  if (!rows.length) return chartEmpty('No enrolled sections are available for the chart.');
  const max = Math.max(...rows.map(row => Number(row.count) || 0), 1);
  return `<div class="chart-title">Students by Section</div><div class="chart-bars">${rows.map(row => `<div class="chart-bar-row"><span class="chart-bar-label">${escapeHtml(row.section)}</span><div class="chart-bar-track"><div class="chart-bar-fill" style="width:${Math.round((Number(row.count) || 0) / max * 100)}%"></div></div><strong>${escapeHtml(row.count)}</strong></div>`).join('')}</div>`;
}

function renderAttendanceGradeChart(rows) {
  if (!rows.length) return chartEmpty('No attendance records are available by grade.');
  const total = rows.reduce((sum, row) => sum + (Number(row.count) || 0), 0) || 1;
  const colors = ['#3B78FF', '#16A34A', '#D97706', '#DC2626', '#7C3AED', '#DB2777'];
  let offset = 0;
  const segments = rows.map((row, index) => {
    const percent = (Number(row.count) || 0) / total;
    const segment = `${percent * 100} ${100 - percent * 100}`;
    const result = `<div class="chart-legend-row"><span class="chart-legend-swatch" style="background:${colors[index % colors.length]}"></span><span>${escapeHtml(row.grade)}</span><strong>${escapeHtml(row.count)} (${Math.round(percent * 100)}%)</strong></div>`;
    offset += percent * 100;
    return result;
  }).join('');
  const gradient = rows.map((row, index) => {
    const percent = (Number(row.count) || 0) / total * 100;
    const start = rows.slice(0, index).reduce((sum, item) => sum + (Number(item.count) || 0), 0) / total * 100;
    return `${colors[index % colors.length]} ${start}% ${start + percent}%`;
  }).join(',');
  return `<div class="chart-title">Attendance by Grade</div><div class="chart-pie-layout"><div class="chart-pie" style="background:conic-gradient(${gradient})" role="img" aria-label="Attendance by grade"></div><div class="chart-legend">${segments}</div></div>`;
}

async function generateStatsReport() {
  const report = await api().get_statistics_report();
  if (!report || report.ok === false) {
    document.getElementById('stats-report').textContent = report && report.message ? report.message : 'Reports are unavailable for the current role.';
    return;
  }
  const now = new Date();
  const ts = now.toLocaleString('en-PH', { year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const rankClass = i => i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : '';
  const maxCnt = report.top_students.length ? report.top_students[0].count : 1;
  const totalGraded = Object.values(report.by_grade).reduce((a, b) => a + b, 0) || 1;

  const div = document.getElementById('stats-report');
  const connection = document.getElementById('stats-connection-summary');
  if (connection) connection.textContent = `System status: ${report.connected ? 'Connected' : 'Disconnected'}`;
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
        <div class="rpt-section-title">Recent Attendance by Date</div>
        <table class="rpt-table">
          <thead><tr><th>Date</th><th>Scans</th></tr></thead>
          <tbody>${report.recent_attendance.map(row => `<tr><td>${escapeHtml(row.date)}</td><td>${escapeHtml(row.count)}</td></tr>`).join('')}</tbody>
        </table>
      </div>

      <div class="rpt-section-block">
        <div class="rpt-section-title">Top Students \u2014 By Attendance Count</div>
        <div class="rpt-ts-line">Generated ${ts}</div>
        <table class="rpt-table">
          <thead><tr><th style="width:32px">#</th><th>Name</th><th>Student LRN</th><th>Grade</th><th>Section</th><th class="rpt-bar-cell">Attendance</th></tr></thead>
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
          <thead><tr><th>Name</th><th>Student LRN</th><th>Grade</th><th>Section</th><th>Records</th></tr></thead>
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
  div.replaceChildren();
  backups.forEach(backup => {
    const item = document.createElement('div');
    item.className = 'report-item';
    item.style.cursor = 'pointer';
    item.addEventListener('click', () => restoreBackup(backup.path));

    const icon = document.createElement('span');
    icon.className = 'report-icon';
    icon.textContent = '\u{1F4BE}';
    const name = document.createElement('span');
    name.className = 'report-name';
    name.textContent = backup.name || '';
    const meta = document.createElement('span');
    meta.className = 'report-meta';
    meta.textContent = `${backup.date || ''} \u00b7 ${backup.size_mb || '?'}`;
    item.append(icon, name, meta);
    div.appendChild(item);
  });
}

async function createBackupNow() {
  if (!guardPermission('backup', 'Creating a backup')) return;
  const res = await api().create_backup();
  alert(res.ok ? res.message : `Backup failed: ${res.message}`);
  loadBackupsList();
}

async function restoreBackup(path) {
  if (!guardPermission('restore', 'Restoring a backup')) return;
  if (!confirm('Restore this backup? The current database will be overwritten.')) return;
  const res = await api().restore_backup(path);
  alert(res.ok ? 'Database restored.' : `Restore failed: ${res.message}`);
  if (res.ok) {
    selectedStudent = null;
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

function resetBlockReason() {
  if (scanning) return 'Stop attendance scanning before resetting the ESP32.';
  if (enrollState && (enrollState.step === 'enrolling' || (enrollState.assignedId && !enrollState.saved))) {
    return 'Finish or cancel fingerprint enrollment before resetting the ESP32.';
  }
  if (pendingDelete || batchDeletePending) return 'Wait for fingerprint deletion to finish before resetting the ESP32.';
  if (window._wipeWait) return 'Wait for fingerprint wiping to finish before resetting the ESP32.';
  return '';
}

async function resetDevice() {
  if (currentRole !== 'admin') {
    alert('Reset Device requires the Administrator role.');
    return;
  }
  if (!connected) {
    alert('Connect to the ESP32 before resetting it.');
    return;
  }
  const blocked = resetBlockReason();
  if (blocked) {
    alert(blocked);
    return;
  }
  const confirmed = await showDestructiveConfirm(
    'Reset Device',
    'This will reboot the ESP32 now. Continue?',
    'Reset Device'
  );
  if (!confirmed) return;
  try {
    const ok = await api().reset_device();
    alert(ok ? 'Reset pulse sent. Watch the Serial Monitor for the new boot banner.' : 'Failed to reset device.');
  } catch (error) {
    alert(`Failed to reset device: ${error && error.message ? error.message : 'unknown error'}.`);
  }
}

async function serialCmd(cmd) {
  if (currentRole !== 'admin') { alert('Serial commands require the Administrator role.'); return; }
  if (!connected) { alert('Connect to the ESP32 first.'); return; }
  smAppend(`> ${cmd}`, 'serial-tx');
  const ok = await api().send_serial_command(cmd);
  if (!ok) smAppend(`! ${cmd} was rejected or could not be sent.`, 'serial-sys');
}
async function sendSerialCmd() {
  if (currentRole !== 'admin') { alert('Serial commands require the Administrator role.'); return; }
  const input = document.getElementById('serial-cmd');
  const val = input.value.trim();
  if (!val) return;
  if (!connected) { alert('Connect to the ESP32 first.'); return; }
  input.value = '';
  smAppend(`> ${val}`, 'serial-tx');
  const ok = await api().send_serial_command(val);
  if (!ok) smAppend(`! ${val} was rejected or could not be sent.`, 'serial-sys');
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
// ── Calendar page (holidays / suspensions / half-days) ──
let calendarViewYear = null;
let calendarViewMonth = null; // 1-12
let calendarEntries = {}; // date -> entry, for the currently-viewed month
let calendarSelectedDate = null;

function calendarShiftMonth(delta) {
  let y = calendarViewYear, m = calendarViewMonth + delta;
  if (m < 1) { m = 12; y -= 1; }
  if (m > 12) { m = 1; y += 1; }
  calendarViewYear = y; calendarViewMonth = m;
  renderCalendarMonth();
}

function calendarGoToday() {
  const now = new Date();
  calendarViewYear = now.getFullYear();
  calendarViewMonth = now.getMonth() + 1;
  renderCalendarMonth();
}

// Fired when the user picks a month/year directly from the native picker
// (clicking the "September 2026" title) instead of stepping with the
// prev/next arrows.
function onCalendarMonthInputChange() {
  const value = document.getElementById('cal-month-input').value; // "YYYY-MM"
  if (!value) return;
  const [y, m] = value.split('-').map(Number);
  if (!y || !m) return;
  calendarViewYear = y;
  calendarViewMonth = m;
  renderCalendarMonth();
}

async function loadCalendarPage() {
  if (!api()) return;
  if (calendarViewYear === null) {
    const now = new Date();
    calendarViewYear = now.getFullYear();
    calendarViewMonth = now.getMonth() + 1;
  }
  await renderCalendarMonth();
}

async function renderCalendarMonth() {
  const grid = document.getElementById('cal-grid');
  const monthInput = document.getElementById('cal-month-input');
  if (!grid || !monthInput) return;
  monthInput.value = `${calendarViewYear}-${String(calendarViewMonth).padStart(2, '0')}`;

  const result = await api().get_calendar_month(calendarViewYear, calendarViewMonth);
  const settings = await api().get_settings();
  calendarEntries = (result && result.ok) ? result.entries : {};
  const noClassWeekdays = new Set((settings && Array.isArray(settings.school_weekdays_off) ? settings.school_weekdays_off : []).map(Number));

  const firstOfMonth = new Date(calendarViewYear, calendarViewMonth - 1, 1);
  const startWeekday = firstOfMonth.getDay(); // 0 = Sunday
  const daysInMonth = new Date(calendarViewYear, calendarViewMonth, 0).getDate();
  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;

  let html = '';
  for (let i = 0; i < startWeekday; i++) html += '<div class="cal-day cal-day-empty"></div>';
  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${calendarViewYear}-${String(calendarViewMonth).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
    const entry = calendarEntries[dateStr];
    const dateObj = new Date(calendarViewYear, calendarViewMonth - 1, day);
    const isToday = dateStr === todayStr;
    const isNoClassRecurringDay = !entry && noClassWeekdays.has(dateObj.getDay());
    let badge = '';
    if (entry) {
      const typeLabel = entry.type === 'half_day' ? 'Half-day' : entry.type === 'suspension' ? 'Suspended' : 'Holiday';
      const shown = entry.label ? escapeHtml(entry.label) : typeLabel;
      badge = `<span class="cal-day-badge cal-badge-${escapeHtml(entry.type)}" title="${escapeHtml(shown)}">${shown}</span>`;
    } else if (isNoClassRecurringDay) {
      badge = '<span class="cal-day-badge cal-badge-no-class" title="No class">No class</span>';
    }
    html += `<div class="cal-day${isToday ? ' cal-day-today' : ''}${isNoClassRecurringDay ? ' cal-day-no-class' : ''}" onclick="openCalendarEntryModal('${dateStr}')">` +
            `<span>${day}</span>${badge}</div>`;
  }
  const totalCells = startWeekday + daysInMonth;
  const trailing = (7 - (totalCells % 7)) % 7;
  for (let i = 0; i < trailing; i++) html += '<div class="cal-day cal-day-empty"></div>';

  grid.innerHTML = html;
}

function openCalendarEntryModal(dateStr) {
  if (!hasPermission('manage_calendar')) return;
  calendarSelectedDate = dateStr;
  const modal = document.getElementById('calendar-entry-modal');
  if (!modal) return;

  const [y, m, d] = dateStr.split('-').map(Number);
  const niceDate = new Date(y, m - 1, d).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
  document.getElementById('calendar-entry-date-label').textContent = niceDate;
  document.getElementById('calendar-entry-error').textContent = '';

  const entry = calendarEntries[dateStr];
  const removeBtn = document.getElementById('cal-entry-remove-btn');
  document.querySelectorAll('input[name="cal-entry-type"]').forEach(r => { r.checked = false; });

  if (entry) {
    const radio = document.querySelector(`input[name="cal-entry-type"][value="${entry.type}"]`);
    if (radio) radio.checked = true;
    document.getElementById('cal-entry-label').value = entry.label || '';
    document.getElementById('cal-entry-time-in').value = entry.time_in || '';
    document.getElementById('cal-entry-time-out').value = entry.time_out || '';
    removeBtn.hidden = false;
  } else {
    document.querySelector('input[name="cal-entry-type"][value="holiday"]').checked = true;
    document.getElementById('cal-entry-label').value = '';
    document.getElementById('cal-entry-time-in').value = '';
    document.getElementById('cal-entry-time-out').value = '';
    removeBtn.hidden = true;
  }
  onCalendarEntryTypeChange();
  modal.hidden = false;
}

function closeCalendarEntryModal() {
  const modal = document.getElementById('calendar-entry-modal');
  if (modal) modal.hidden = true;
  calendarSelectedDate = null;
}

function onCalendarEntryTypeChange() {
  const selected = document.querySelector('input[name="cal-entry-type"]:checked');
  const timesWrap = document.getElementById('cal-half-day-times');
  timesWrap.hidden = !selected || selected.value !== 'half_day';
}

async function saveCalendarEntry() {
  if (!calendarSelectedDate) return;
  const selected = document.querySelector('input[name="cal-entry-type"]:checked');
  const error = document.getElementById('calendar-entry-error');
  if (!selected) { error.textContent = 'Choose a type.'; return; }

  const label = document.getElementById('cal-entry-label').value;
  const timeIn = document.getElementById('cal-entry-time-in').value;
  const timeOut = document.getElementById('cal-entry-time-out').value;

  const result = await api().set_calendar_entry(calendarSelectedDate, selected.value, label, timeIn, timeOut);
  if (!result.ok) {
    error.textContent = result.message || 'Could not save this entry.';
    return;
  }
  closeCalendarEntryModal();
  await renderCalendarMonth();
}

async function removeCalendarEntry() {
  if (!calendarSelectedDate) return;
  const result = await api().remove_calendar_entry(calendarSelectedDate);
  if (!result.ok) {
    document.getElementById('calendar-entry-error').textContent = result.message || 'Could not remove this entry.';
    return;
  }
  closeCalendarEntryModal();
  await renderCalendarMonth();
}

async function loadSettingsPage() {
  if (!api()) return;
  const s = await api().get_settings();
  document.getElementById('set-auto-reconnect').classList.toggle('on', !!s.auto_reconnect);
  document.getElementById('set-auto-detect').classList.toggle('on', !!s.auto_detect_serial);
  applyTheme(s.theme);
  applyCompact(!!s.compact_sidebar);
  document.getElementById('set-school-name').value = s.school_name || '';
  document.getElementById('set-cooldown').value = s.cooldown;
  document.getElementById('set-confidence').value = s.min_confidence;
  const session = await api().get_session_state();
  applySessionState(session);
  document.getElementById('set-log-to-file').classList.toggle('on', !!s.log_to_file);
  document.getElementById('set-debug-logging').classList.toggle('on', !!s.enable_debug_logging);
  document.getElementById('set-log-folder').textContent = s.log_folder || '\u2014';
  document.getElementById('set-backup-interval').value = s.auto_backup_interval_minutes;
  document.getElementById('set-last-backup').textContent = s.last_backup || 'No backups yet';
  // Attendance time rules
  document.getElementById('set-time-in').value = s.time_in || '08:00';
  document.getElementById('set-time-out').value = s.time_out || '17:00';
  document.getElementById('set-early-threshold').value = s.early_threshold_minutes || 15;
  document.getElementById('set-late-threshold').value = s.late_threshold_minutes || 15;
  document.getElementById('set-absent-threshold').value = s.absent_threshold_minutes || 0;

  await refreshConnectedDevicePanel();
  await refreshPortList();
  populateBaudOptions(s.baud_rate);
  const portInput = document.getElementById('set-port-override');
  if (portInput) portInput.value = s.com_port || '';
}

let settingsSaveTimer = null;
const AUTO_SAVE_SETTING_IDS = new Set([
  'set-port-override', 'set-baud-rate-select', 'set-auto-reconnect', 'set-auto-detect',
  'set-theme', 'settings-compact-toggle', 'set-cooldown', 'set-confidence',
  'set-log-to-file', 'set-debug-logging', 'set-time-in', 'set-time-out',
  'set-early-threshold', 'set-late-threshold', 'set-absent-threshold', 'set-backup-interval',
]);

function scheduleSettingsSave() {
  if (currentRole !== 'admin') return;
  clearTimeout(settingsSaveTimer);
  const status = document.getElementById('settings-save-status');
  if (status) status.textContent = 'Saving...';
  settingsSaveTimer = setTimeout(() => saveSettings(true), 400);
}

document.addEventListener('input', event => {
  if (AUTO_SAVE_SETTING_IDS.has(event.target.id)) scheduleSettingsSave();
});
document.addEventListener('change', event => {
  if (AUTO_SAVE_SETTING_IDS.has(event.target.id)) scheduleSettingsSave();
});
document.addEventListener('click', event => {
  if (AUTO_SAVE_SETTING_IDS.has(event.target.id)) scheduleSettingsSave();
});

// Shared by the Settings page's connection panel AND the setup wizard's
// device step, so both show identical detail instead of two different
// (and potentially drifting) renderings of the same connection info.
function formatDeviceStatusLines(status) {
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
  return lines;
}

async function refreshConnectedDevicePanel() {
  const status = await api().get_connection_status();
  const pill = document.getElementById('conn-device-status');
  const detail = document.getElementById('conn-device-detail');
  if (status.connected) {
    pill.textContent = '\u25cf Connected';
    pill.className = 'conn-status-pill connected';
    const lines = formatDeviceStatusLines(status);
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

async function saveSettings(silent = false) {
  if (currentRole !== 'admin') {
    return;
  }
  const payload = {
    com_port: document.getElementById('set-port-override').value.trim(),
    baud_rate: parseInt(document.getElementById('set-baud-rate-select').value, 10),
    theme: document.getElementById('set-theme').value,
    school_name: document.getElementById('set-school-name').value.trim(),
    auto_reconnect: document.getElementById('set-auto-reconnect').classList.contains('on'),
    auto_detect_serial: document.getElementById('set-auto-detect').classList.contains('on'),
    compact_sidebar: document.getElementById('settings-compact-toggle').classList.contains('on'),
    cooldown: parseInt(document.getElementById('set-cooldown').value, 10),
    min_confidence: parseInt(document.getElementById('set-confidence').value, 10),
    log_to_file: document.getElementById('set-log-to-file').classList.contains('on'),
    enable_debug_logging: document.getElementById('set-debug-logging').classList.contains('on'),
    auto_backup_interval_minutes: parseInt(document.getElementById('set-backup-interval').value, 10),
    current_role: currentRole,
    // Attendance time rules
    time_in: document.getElementById('set-time-in').value || '08:00',
    time_out: document.getElementById('set-time-out').value || '17:00',
    early_threshold_minutes: parseInt(document.getElementById('set-early-threshold').value, 10) || 15,
    late_threshold_minutes: parseInt(document.getElementById('set-late-threshold').value, 10) || 15,
    absent_threshold_minutes: parseInt(document.getElementById('set-absent-threshold').value, 10) || 0,
  };
  const res = await api().save_ui_settings(payload);
  const status = document.getElementById('settings-save-status');
  if (!res.ok) {
    if (!silent) alert(`Settings could not be saved: ${res.message}`);
    if (status) status.textContent = 'Could not save changes';
    return;
  }
  applyCompact(payload.compact_sidebar);
  applyTheme(payload.theme);
  applySchoolName(payload.school_name);
  if (status) status.textContent = 'All changes saved';
}

async function restoreDefaultSettings() {
  if (currentRole !== 'admin') {
    alert('Administrator authentication is required to restore defaults.');
    return;
  }
  if (!await showDestructiveConfirm('Restore Defaults', 'Reset all application settings to their default values?', 'Restore Defaults')) return;
  const result = await api().restore_default_settings();
  if (!result.ok) {
    alert(result.message || 'Could not restore defaults.');
    return;
  }
  await loadSettingsPage();
}

function openLogFolder() { api().open_log_folder(); }

// ── User Role ──
const ROLE_LABELS = { admin: 'Administrator', teacher: 'Teacher', guest: 'Guest' };

function paintTitlebarRole(key) {
  const badge = document.getElementById('titlebar-role');
  if (!badge) return;
  badge.className = 'tb-role-badge role-' + key;
  badge.value = key;
}

function updateRole() {
  const key = document.getElementById('role-select').value;
  requestRoleChange(key);
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

let lastActivitySentAt = 0;
function noteUserActivity() {
  if (!api() || currentRole === 'guest') return;
  const now = Date.now();
  if (now - lastActivitySentAt < 30000) return;
  lastActivitySentAt = now;
  api().touch_session().then(state => {
    if (state.role !== currentRole) applySessionState(state);
  });
}

document.addEventListener('pointerdown', noteUserActivity);
document.addEventListener('keydown', noteUserActivity);

// ── Boot ──
tick();
setInterval(tick, 1000);
whenApiReady(() => {
  loadDashboard();
  api().get_settings().then(s => {
    applyTheme(s.theme);
    applyCompact(!!s.compact_sidebar);
    applySchoolName(s.school_name);
  });
  runSetupWizardRouter();
  sessionTouchTimer = setInterval(async () => {
    const state = await api().get_session_state();
    if (state.role !== currentRole) {
      applySessionState(state);
      if (state.role === 'guest') alert('Your session was locked after inactivity.');
    }
  }, 10000);
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
