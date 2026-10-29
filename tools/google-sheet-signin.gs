/**
 * BK Stays guidebook sign-ins -> Google Sheet.
 * Paste into the Sheet: Extensions > Apps Script. Deploy > New deployment > Web app,
 * Execute as: Me, Who has access: Anyone. Put the Web app URL in content/settings.json ("signinUrl").
 * Each property gets its own tab (created automatically).
 */
const HEADERS = ['First Name', 'Last Name', 'Email', 'Signed In (UTC)', 'Property'];

function doPost(e) {
  const p = (e && e.parameter) || {};
  if (p['bot-field']) return ContentService.createTextOutput('ok');
  const email = String(p.email || '').trim();
  if (!email || email.indexOf('@') < 1) return ContentService.createTextOutput('ignored');
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const name = String(p.property || 'Unknown').slice(0, 90);
    let sh = ss.getSheetByName(name);
    if (!sh) {
      const blank = ss.getSheets().find((s) => s.getLastRow() <= 1 && s.getName() === 'Untitled');
      sh = blank ? blank.setName(name) : ss.insertSheet(name);
      sh.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]).setFontWeight('bold');
      sh.setFrozenRows(1);
    }
    if (sh.getLastRow() === 0) {
      sh.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]).setFontWeight('bold');
      sh.setFrozenRows(1);
    }
    const when = p.signed_in_at ? new Date(p.signed_in_at) : new Date();
    sh.appendRow([
      String(p.first_name || '').slice(0, 80),
      String(p.last_name || '').slice(0, 80),
      email.slice(0, 120),
      Utilities.formatDate(when, 'UTC', 'yyyy-MM-dd HH:mm'),
      name,
    ]);
  } finally {
    lock.releaseLock();
  }
  return ContentService.createTextOutput('ok');
}
