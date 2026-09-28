const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const sourcePath = path.join(__dirname, '..', 'python', 'gui_web', 'web', 'app.js');
const source = fs.readFileSync(sourcePath, 'utf8');
const functionStart = source.indexOf('async function loadAttendancePage() {');
const functionEnd = source.indexOf('\nfunction renderAttendanceRows', functionStart);

assert.notEqual(functionStart, -1, 'loadAttendancePage must exist in app.js');
assert.notEqual(functionEnd, -1, 'loadAttendancePage must have a following function boundary');

function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
}

async function main() {
  const requests = [deferred(), deferred()];
  const rendered = [];
  let requestIndex = 0;
  const nodes = {
    'att-mode': { value: 'Today' },
    'att-count': { textContent: '' },
    'att-page-sep': { style: {} },
    'att-prev-btn': { style: {}, disabled: false },
    'att-next-btn': { style: {}, disabled: false },
  };
  const context = {
    attendanceOffset: 0,
    attendanceLoadRequestId: 0,
    api: () => ({
      get_attendance: () => requests[requestIndex++].promise,
    }),
    document: { getElementById: id => nodes[id] },
    renderAttendanceRows: rows => rendered.push(rows[0].label),
  };
  const functionSource = source.slice(functionStart, functionEnd);
  vm.runInNewContext(`${functionSource}; this.loadAttendancePage = loadAttendancePage;`, context);

  const olderRequest = context.loadAttendancePage();
  const newerRequest = context.loadAttendancePage();

  requests[1].resolve({ rows: [{ label: 'newest' }], has_more: false });
  await newerRequest;
  requests[0].resolve({ rows: [{ label: 'stale' }], has_more: false });
  await olderRequest;

  assert.deepEqual(rendered, ['newest'], 'a stale response must not overwrite the newest attendance data');
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});