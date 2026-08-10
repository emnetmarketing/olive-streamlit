/** Olive Streamlit - Google Sheets Web App storage */
const SPREADSHEET_ID = '1u3NE0rDElnhfYZ2sv2iLy22juLa2z5fBR5xmUgKznBo';

const SHEET_HEADERS = Object.freeze({
  settings: ['key', 'value_json', 'description', 'updated_at', 'updated_by'],
  analysis_results: [
    'result_id', 'created_at', 'created_by', 'period_start', 'period_end',
    'metrics_json', 'filters_json', 'result_json'
  ],
  audit_logs: ['log_id', 'created_at', 'actor', 'action', 'target', 'details_json']
});

function doGet() {
  try {
    return jsonResponse_({ ok: true, data: ensureSchema_() });
  } catch (error) {
    return jsonResponse_({ ok: false, error: safeError_(error) });
  }
}

function doPost(event) {
  const lock = LockService.getScriptLock();
  try {
    lock.waitLock(30000);
    const body = JSON.parse((event && event.postData && event.postData.contents) || '{}');
    return jsonResponse_({ ok: true, data: handleAction_(body) });
  } catch (error) {
    return jsonResponse_({ ok: false, error: safeError_(error) });
  } finally {
    if (lock.hasLock()) lock.releaseLock();
  }
}

function handleAction_(request) {
  const action = String(request.action || '');
  switch (action) {
    case 'ensure_schema':
      return ensureSchema_();
    case 'records':
      return records_(request.sheet);
    case 'append_record':
      appendRecord_(request.sheet, request.data || {});
      return { saved: true };
    case 'update_record':
      updateRecord_(request.sheet, request.row_number, request.changes || {});
      return { updated: true };
    case 'delete_record':
      deleteRecord_(request.sheet, request.row_number);
      return { deleted: true };
    default:
      throw new Error('허용되지 않은 action입니다.');
  }
}

function spreadsheet_() {
  return SpreadsheetApp.openById(SPREADSHEET_ID);
}

function expectedHeaders_(name) {
  if (!Object.prototype.hasOwnProperty.call(SHEET_HEADERS, name)) {
    throw new Error('허용되지 않은 시트입니다: ' + name);
  }
  return SHEET_HEADERS[name];
}

function ensureSheet_(name) {
  const headers = expectedHeaders_(name);
  const book = spreadsheet_();
  let sheet = book.getSheetByName(name);
  if (!sheet) sheet = book.insertSheet(name);

  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.setFrozenRows(1);
    return sheet;
  }

  const current = sheet.getRange(1, 1, 1, headers.length).getDisplayValues()[0];
  if (JSON.stringify(current) !== JSON.stringify(headers)) {
    throw new Error("'" + name + "' 시트의 1행 헤더가 Code.gs의 구조와 다릅니다. 기존 데이터는 변경하지 않았습니다.");
  }
  return sheet;
}

function ensureSchema_() {
  const counts = {};
  Object.keys(SHEET_HEADERS).forEach(function(name) {
    const sheet = ensureSheet_(name);
    counts[name] = Math.max(0, sheet.getLastRow() - 1);
  });
  return counts;
}

function records_(name) {
  const sheet = ensureSheet_(name);
  const headers = expectedHeaders_(name);
  const rowCount = sheet.getLastRow() - 1;
  if (rowCount <= 0) return [];
  const values = sheet.getRange(2, 1, rowCount, headers.length).getDisplayValues();
  return values.map(function(row) {
    const record = {};
    headers.forEach(function(header, index) {
      record[header] = row[index] || '';
    });
    return record;
  });
}

function appendRecord_(name, data) {
  const sheet = ensureSheet_(name);
  const headers = expectedHeaders_(name);
  const row = headers.map(function(header) { return cellValue_(data[header]); });
  sheet.getRange(sheet.getLastRow() + 1, 1, 1, headers.length).setValues([row]);
}

function updateRecord_(name, rowNumber, changes) {
  const sheet = ensureSheet_(name);
  const headers = expectedHeaders_(name);
  const row = Number(rowNumber);
  if (!Number.isInteger(row) || row < 2 || row > sheet.getLastRow()) {
    throw new Error('수정할 행 번호가 올바르지 않습니다.');
  }
  Object.keys(changes).forEach(function(key) {
    if (headers.indexOf(key) < 0) throw new Error('허용되지 않은 컬럼입니다: ' + key);
  });
  const values = sheet.getRange(row, 1, 1, headers.length).getDisplayValues()[0];
  Object.keys(changes).forEach(function(key) {
    values[headers.indexOf(key)] = cellValue_(changes[key]);
  });
  sheet.getRange(row, 1, 1, headers.length).setValues([values]);
}

function deleteRecord_(name, rowNumber) {
  const sheet = ensureSheet_(name);
  const row = Number(rowNumber);
  if (!Number.isInteger(row) || row < 2 || row > sheet.getLastRow()) {
    throw new Error('삭제할 행 번호가 올바르지 않습니다.');
  }
  sheet.deleteRow(row);
}

function cellValue_(value) {
  if (value === null || typeof value === 'undefined') return '';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function jsonResponse_(body) {
  return ContentService.createTextOutput(JSON.stringify(body))
    .setMimeType(ContentService.MimeType.JSON);
}

function safeError_(error) {
  return error && error.message ? String(error.message) : '알 수 없는 오류';
}
