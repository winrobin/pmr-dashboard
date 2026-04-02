var TARGET="pmr_table";var SOURCE="raw_json";
function cell(v){if(v===null||v===undefined)return "";if(typeof v==="boolean")return v?"TRUE":"FALSE";return String(v).replace(/\\n/g,"\n");}
function pmrImport(){var ss=SpreadsheetApp.getActiveSpreadsheet();
var src=ss.getSheetByName(SOURCE);if(!src){Browser.msgBox("raw_json not found");return;}
var raw=src.getRange("A1").getValue();if(!raw||raw.toString().trim().length<10){Browser.msgBox("Paste JSON into raw_json!A1 first");return;}
var data;try{data=JSON.parse(raw.toString());}catch(e){Browser.msgBox("JSON error: "+e.message);return;}
if(!Array.isArray(data)||data.length===0){Browser.msgBox("Not an array or empty");return;}
var ts=ss.getSheetByName(TARGET);if(!ts){ts=ss.insertSheet(TARGET);}ts.clear();
var H=["#","ID","Property Name","Location","Asking Price (AUD)","Net Income (AUD)","Multiplier","Est. Net Income","Est. Multiplier","Contract Years","BC Salary (AUD)","BC Salary %","Letting Pool Units","Total Units","Ext. Units Recoverable","$Wk/Unit","Est. Net Yield (%)","On-Site","Property Purchase","Rating Score","Rating Basis","Data Gaps","Next Action","Data Source","Source URL","Tender Deadline"];
var rows=[H];
for(var i=0;i<data.length;i++){var d=data[i];
rows.push([i+1,cell(d.id),cell(d.propertyName),cell(d.location),cell(d.askingPrice),cell(d.netIncome),cell(d.multiplier),cell(d.estimatedNetIncome),cell(d.estimatedMultiplier),cell(d.contractYearsRemaining),cell(d.bcSalary),cell(d.bcSalaryPercent),cell(d.lettingPoolUnits),cell(d.totalUnits),cell(d.externalUnitsRecoverable),cell(d.weeklyLettingIncomePerUnit),cell(d.estimatedNetYield),cell(d.onSiteRequired),cell(d.propertyPurchaseRequired),cell(d.ratingScore),cell(d.ratingBasis),cell(d.dataGaps),cell(d.nextAction),cell(d.dataSource),cell(d.sourceUrl),cell(d.tenderDeadline)]);}
ts.getRange(1,1,rows.length,rows[0].length).setValues(rows);
ts.setFrozenRows(1);
Logger.log("Done: "+data.length+" rows");Browser.msgBox("Done! Imported "+data.length+" properties.");}
