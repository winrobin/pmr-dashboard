/**
 * PMR Research Dashboard - Auto-Refresh from Google Drive
 * 
 * Setup:
 * 1. In your Google Sheet: Extensions > Apps Script
 * 2. Paste this entire script
 * 3. Save → Click the clock icon (Triggers) → Add Trigger
 *    - Function: autoRefreshDaily
 *    - Event: Time-driven → Day timer → 9am to 10am
 * 4. Run refreshFromDrive() once manually to authorize
 * 
 * Drive file must be "Anyone with the link can view"
 */

var DRIVE_FILE_ID = '1urDyA-_s_5DmLOhRuW4jueL4YwucB6C0';
var SHEET_RANKING = 'ranking';
var SHEET_RAW = 'raw_data';
var SHEET_DD = 'due_diligence';

function getDriveJson() {
  var url = 'https://drive.google.com/uc?export=download&id=' + DRIVE_FILE_ID;
  var response = UrlFetchApp.fetch(url, {
    muteHttpExceptions: true
  });
  if (response.getResponseCode() !== 200) {
    throw new Error('Cannot read Drive file. Ensure sharing is set to "Anyone with link". Response: ' + response.getResponseCode());
  }
  var text = response.getContentText();
  return JSON.parse(text);
}

function refreshFromDrive() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var data = getDriveJson();

  Logger.log('Fetched ' + data.length + ' properties');

  refreshRanking(ss, data);
  refreshRawData(ss, data);
  refreshDueDiligence(ss, data);
  applyConditionalFormatting(ss, data.length);

  Logger.log('✅ Refresh complete');
}

function refreshRanking(ss, data) {
  var sheet = ss.getSheetByName(SHEET_RANKING);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_RANKING);
  } else {
    sheet.clear();
  }

  var headers = ['propertyName','location','askingPrice','netIncome','multiplier',
    'contractYearsRemaining','bcSalaryPercent','lettingPoolUnits',
    'weeklyLettingIncomePerUnit','ratingScore','ratingBasis','nextAction','discoveredDate'];

  var rows = data.map(function(d) {
    return [
      d.propertyName, d.location, d.askingPrice, d.netIncome,
      d.multiplier, d.contractYearsRemaining, d.bcSalaryPercent,
      d.lettingPoolUnits, d.weeklyLettingIncomePerUnit,
      d.ratingScore, d.ratingBasis, d.nextAction, d.discoveredDate || ''
    ];
  });

  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);

  // Sort by ratingScore descending
  if (rows.length > 1) {
    sheet.getRange(2, 1, rows.length, headers.length)
      .sort({column: 10, ascending: false});
  }

  // Format numbers
  sheet.getRange(2, 3, rows.length, 1).setNumberFormat('$#,##0');   // askingPrice
  sheet.getRange(2, 4, rows.length, 1).setNumberFormat('$#,##0');   // netIncome
  sheet.getRange(2, 5, rows.length, 1).setNumberFormat('0.00');     // multiplier
  sheet.getRange(2, 10, rows.length, 1).setNumberFormat('0.0');     // ratingScore

  // Column widths
  sheet.setColumnWidth(1, 220);
  sheet.setColumnWidth(2, 250);
  sheet.setColumnWidth(11, 300);  // ratingBasis
  sheet.setColumnWidth(12, 250);  // nextAction

  sheet.setFrozenRows(1);
}

function refreshRawData(ss, data) {
  var sheet = ss.getSheetByName(SHEET_RAW);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_RAW);
  } else {
    sheet.clear();
  }

  var headers = ['id','propertyName','location','askingPrice','netIncome','multiplier',
    'estimatedNetIncome','estimatedMultiplier','contractYearsRemaining',
    'bcSalary','bcSalaryPercent','lettingPoolUnits','totalUnits',
    'externalUnitsRecoverable','weeklyLettingIncomePerUnit',
    'estimatedNetYield','ratingScore','ratingBasis','dataGaps',
    'nextAction','dataSource','sourceUrl','tenderDeadline','discoveredDate'];

  var rows = data.map(function(d) {
    return [
      d.id, d.propertyName, d.location,
      d.askingPrice, d.netIncome, d.multiplier,
      d.estimatedNetIncome, d.estimatedMultiplier,
      d.contractYearsRemaining, d.bcSalary, d.bcSalaryPercent,
      d.lettingPoolUnits, d.totalUnits,
      d.externalUnitsRecoverable, d.weeklyLettingIncomePerUnit,
      d.estimatedNetYield, d.ratingScore,
      d.ratingBasis, d.dataGaps, d.nextAction,
      d.dataSource, d.sourceUrl, d.tenderDeadline,
      d.discoveredDate || ''
    ];
  });

  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);

  // Format numbers
  sheet.getRange(2, 4, rows.length, 1).setNumberFormat('$#,##0');  // askingPrice
  sheet.getRange(2, 5, rows.length, 1).setNumberFormat('$#,##0');  // netIncome
  sheet.getRange(2, 7, rows.length, 1).setNumberFormat('$#,##0');  // estimatedNetIncome
  sheet.getRange(2, 10, rows.length, 1).setNumberFormat('$#,##0'); // bcSalary

  // Column widths
  sheet.setColumnWidth(2, 200);
  sheet.setColumnWidth(3, 200);
  sheet.setColumnWidth(18, 300); // ratingBasis
  sheet.setColumnWidth(19, 300); // dataGaps
  sheet.setColumnWidth(22, 300); // sourceUrl

  sheet.setFrozenRows(1);
}

function refreshDueDiligence(ss, data) {
  var sheet = ss.getSheetByName(SHEET_DD);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_DD);
  } else {
    sheet.clear();
  }

  var headers = ['propertyName', 'dataGaps', 'nextAction', 'sourceUrl', 'discoveredDate'];
  var rows = data.map(function(d) {
    return [d.propertyName, d.dataGaps, d.nextAction, d.sourceUrl, d.discoveredDate || ''];
  });

  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);

  sheet.setColumnWidth(1, 220);
  sheet.setColumnWidth(2, 350);
  sheet.setColumnWidth(3, 300);
  sheet.setColumnWidth(4, 300);

  sheet.setFrozenRows(1);
}

function applyConditionalFormatting(ss, rowCount) {
  var sheet = ss.getSheetByName(SHEET_RANKING);
  if (!sheet) return;
  if (!rowCount) {
    var lastRow = sheet.getLastRow();
    rowCount = lastRow > 1 ? lastRow - 1 : 7;
  }
  var rules = [];

  // BC% > 80 → Red
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThan(80)
    .setBackground('#fce8e6').setFontColor('#d93025')
    .setRanges([sheet.getRange(2, 7, rowCount, 1)])
    .build());

  // BC% 60-70 → Green
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenNumberBetween(60, 70)
    .setBackground('#e6f4ea').setFontColor('#1b9e77')
    .setRanges([sheet.getRange(2, 7, rowCount, 1)])
    .build());

  // Multiplier ≤ 5 → Green
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenNumberLessThanOrEqualTo(5)
    .setBackground('#e6f4ea').setFontColor('#1b9e77')
    .setRanges([sheet.getRange(2, 5, rowCount, 1)])
    .build());

  // $/wk < 40 → Red
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenNumberLessThan(40)
    .setBackground('#fce8e6').setFontColor('#d93025')
    .setRanges([sheet.getRange(2, 9, rowCount, 1)])
    .build());

  // Rating ≥ 3.5 → Green
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThanOrEqualTo(3.5)
    .setBackground('#e6f4ea').setFontColor('#1b9e77')
    .setRanges([sheet.getRange(2, 10, rowCount, 1)])
    .build());

  // Rating < 2.5 → Red
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenNumberLessThan(2.5)
    .setBackground('#fce8e6').setFontColor('#d93025')
    .setRanges([sheet.getRange(2, 10, rowCount, 1)])
    .build());

  sheet.setConditionalFormatRules(rules);
}

function autoRefreshDaily() {
  try {
    refreshFromDrive();
  } catch (e) {
    Logger.log('Error: ' + e.message);
  }
}
