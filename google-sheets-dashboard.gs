/**
 * PMR Research Dashboard - One-Click Setup
 *
 * Instructions:
 * 1. Create a new Google Sheet at https://sheets.new
 * 2. Extensions > Apps Script
 * 3. Paste this entire script
 * 4. Click 💾 Save
 * 5. Change function dropdown to "setupDashboard" and click ▶ Run
 * 6. Authorize when prompted
 * 7. Done — 3 tabs, data, formatting, filters
 */

function setupDashboard() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  ss.setName("PMR Research Dashboard");

  // Delete default sheet if exists
  var def = ss.getSheets()[0];
  if (ss.getSheets().length > 1 || def.getName() === "Sheet1") {
    if (ss.getSheets().length === 1) def.setName("__temp__");
  }

  // Data source
  var D = [
    {
      id: "BW-001",
      propertyName: "The Gap · Townhouse Complex",
      location: "Brisbane Inner West (The Gap), QLD",
      askingPrice: 790000,
      netIncome: 128133,
      multiplier: 6.17,
      estimatedNetIncome: null,
      estimatedMultiplier: null,
      contractYearsRemaining: 23,
      bcSalary: 78819,
      bcSalaryPercent: 61.5,
      lettingPoolUnits: 14,
      totalUnits: null,
      externalUnitsRecoverable: 12,
      weeklyLettingIncomePerUnit: 68,
      estimatedNetYield: 16.2,
      onSiteRequired: false,
      propertyPurchaseRequired: false,
      ratingScore: 4.2,
      ratingBasis: "BC薪资占比61.5%健康(60-70%为理想区间); 合同剩23年极安全; 每单元$68/周佣金合理(布市正常$60-85); Letting Pool 13+1 另有12外部单元可收回=增长空间大; Caretaking极简无Gate/泳池。唯一不足是倍数6.17x略高于PMR常规3-5x",
      dataGaps: "楼龄：未知\nLetting Pool占总套数比例：总套数未知\n短租/长租：标注全部为Permanent Rentals\n12外部单元收回可能性：非承诺数据，需咨询Body Corporate确认",
      nextAction: "核实12外部单元收回概率; 获取总套数计算Pool占比; 确认楼龄",
      dataSource: "Accom Properties ID 9222 (Mar 2026)",
      sourceUrl: "https://accomproperties.com.au/business-display/business-the-gap,19190",
      tenderDeadline: null
    },
    {
      id: "WE-001",
      propertyName: "West End Business-Only MR",
      location: "West End, QLD",
      askingPrice: 750000,
      netIncome: 125078,
      multiplier: 5.99,
      estimatedNetIncome: null,
      estimatedMultiplier: null,
      contractYearsRemaining: null,
      bcSalary: 76478,
      bcSalaryPercent: 61.1,
      lettingPoolUnits: null,
      totalUnits: null,
      externalUnitsRecoverable: null,
      weeklyLettingIncomePerUnit: null,
      estimatedNetYield: 16.7,
      onSiteRequired: false,
      propertyPurchaseRequired: false,
      ratingScore: 3.9,
      ratingBasis: "BC薪资$76K占净利61.1%健康; CPI递增很稳定; 楼龄新(推估2018-2021)降维护风险。但Letting Pool数量/总收入完全未披露=主要风险",
      dataGaps: "Letting Pool数量：Listing未提及\n总套数：未知\n合同剩余年限：未知\n楼龄：仅根据推估为2018-2021，需Body Corporate核实\n长租/短租：未知\n每单元每周佣金：无法计算",
      nextAction: "索取Letting Pool明细、合同年限确认、楼龄确认",
      dataSource: "Accom Properties (Mar 2026)",
      sourceUrl: "https://accomproperties.com.au/business-display/business-west-end,19008",
      tenderDeadline: null
    },
    {
      id: "CH-001",
      propertyName: "Chermside/Lutwyche Dual Complex",
      location: "Chermside & Lutwyche, QLD (~4km apart)",
      askingPrice: 652000,
      netIncome: null,
      multiplier: null,
      estimatedNetIncome: 178052,
      estimatedMultiplier: 3.66,
      contractYearsRemaining: null,
      bcSalary: 90000,
      bcSalaryPercent: null,
      lettingPoolUnits: null,
      totalUnits: null,
      externalUnitsRecoverable: null,
      weeklyLettingIncomePerUnit: null,
      estimatedNetYield: null,
      onSiteRequired: false,
      propertyPurchaseRequired: false,
      ratingScore: 3.5,
      ratingBasis: "$652K门槛很低; 两栋极简设施(无泳池/BBQ)降低维护; BC薪资$90K+。但因净利未官方披露、倍数不可准确计算，需财报验证。若$178K属实则实际回报率高达27.3%、倍数仅3.66x=极优",
      dataGaps: "年净收入：未官方披露。网传$178K非卖方确认\n实际倍数：无法计算(净利未知)。估算3.66x仅供参考\nBC薪资占净利比：净利未知故比率不可靠\n合同剩余年限：仅知'长期协议'，需具体年数\nLetting Pool：未知\n总套数：未知(两栋合计)\n楼龄：仅描述为'现代建筑'(modern)，具体年份未知",
      nextAction: "联系Accom Properties/TheOnsiteManager获取完整信息表及确认净利",
      dataSource: "TheOnsiteManager.com.au (Mar 2026)",
      sourceUrl: "https://theonsitemanager.com.au/",
      tenderDeadline: null
    },
    {
      id: "KP-001",
      propertyName: "Silver Quays",
      location: "Kangaroo Point, QLD",
      askingPrice: 691155,
      netIncome: 138231,
      multiplier: 5.0,
      estimatedNetIncome: null,
      estimatedMultiplier: null,
      contractYearsRemaining: null,
      bcSalary: 129395,
      bcSalaryPercent: 93.6,
      lettingPoolUnits: 5,
      totalUnits: 49,
      externalUnitsRecoverable: null,
      weeklyLettingIncomePerUnit: 34,
      estimatedNetYield: 20.0,
      onSiteRequired: false,
      propertyPurchaseRequired: false,
      ratingScore: 2.0,
      ratingBasis: "回报率20%表面看不错，但拆解发现BC薪资占93.6%——这本质上是caretaker工作而非PMR投资。Letting Pool仅5单元/49单元=10.2%，且每单元每周仅$34(正常应$60-85)。$34/周极不正常，可能暗示BC薪资被高估或净收入计算有误。几乎无出租增长空间",
      dataGaps: "合同剩余年限：Listing未披露\n楼龄：未知\n3年财务趋势：需向卖方索取财报\n长租/短租：未知\nBC薪资$129K是否含GST：Listing未明确\nLetting收入$8,836是否准确：需财报核实",
      nextAction: "要求经纪人(Resort Brokers)提供3年财报验证BC薪资和出租收入数据",
      dataSource: "Accom Properties (Updated Mar 27, 2026)",
      sourceUrl: "https://accomproperties.com.au/business-display/business-kangaroo-point,19211",
      tenderDeadline: null
    },
    {
      id: "BC-001",
      propertyName: "Brisbane City Permanent MR",
      location: "Brisbane City, QLD",
      askingPrice: 608000,
      netIncome: null,
      multiplier: null,
      estimatedNetIncome: null,
      estimatedMultiplier: null,
      contractYearsRemaining: null,
      bcSalary: null,
      bcSalaryPercent: null,
      lettingPoolUnits: null,
      totalUnits: null,
      externalUnitsRecoverable: null,
      weeklyLettingIncomePerUnit: null,
      estimatedNetYield: null,
      onSiteRequired: false,
      propertyPurchaseRequired: false,
      ratingScore: 2.5,
      ratingBasis: "门槛$608K最低，Spare Time管理灵活; 但净收入/BC/Letting Pool全未披露，信息严重缺失，风险不可控。需获取财报后重评",
      dataGaps: "年净收入：经纪人未披露，必须索取3年会计核实财报\nBC薪资：未知\n合同剩余年限：未知，需Agreement副本\nLetting Pool数量：未知\n总套数：未知\n楼龄：未知",
      nextAction: "向经纪人索取完整信息披露表（含3年财报、合同摘要、Letting Pool明细）",
      dataSource: "Accom Properties (Mar 2026)",
      sourceUrl: "https://accomproperties.com.au/business-display/business-brisbane-city,19124",
      tenderDeadline: null
    },
    {
      id: "TF-001",
      propertyName: "Teneriffe Blue-Chip MR",
      location: "Teneriffe, QLD",
      askingPrice: 1356768,
      netIncome: null,
      multiplier: null,
      estimatedNetIncome: null,
      estimatedMultiplier: null,
      contractYearsRemaining: null,
      bcSalary: null,
      bcSalaryPercent: null,
      lettingPoolUnits: null,
      totalUnits: null,
      externalUnitsRecoverable: null,
      weeklyLettingIncomePerUnit: null,
      estimatedNetYield: null,
      onSiteRequired: false,
      propertyPurchaseRequired: false,
      ratingScore: 2.5,
      ratingBasis: "蓝钻地段极优(距CBD近、Riverwalk直达); 但$1.36M超第一档范围; 净收入/BC/合同条款完全缺失。评分仅基于地段价值。需完整披露后再评估",
      dataGaps: "年净收入：完全未披露，必须获取财报\nBC薪资：未知\n合同条款及剩余年限：未知\nLetting Pool：未知\n总套数：未知\nOffice Hours要求：未知",
      nextAction: "向经纪人(ResortBrokers)要求完整信息披露包后决定是否尽调",
      dataSource: "Accom Properties (Mar 2026)",
      sourceUrl: "https://accomproperties.com.au/business-display/business-teneriffe,19064",
      tenderDeadline: null
    },
    {
      id: "BC-002",
      propertyName: "Brisbane City Premier (Tender)",
      location: "Brisbane City, QLD",
      askingPrice: null,
      netIncome: null,
      multiplier: null,
      estimatedNetIncome: null,
      estimatedMultiplier: null,
      contractYearsRemaining: null,
      bcSalary: null,
      bcSalaryPercent: null,
      lettingPoolUnits: null,
      totalUnits: null,
      externalUnitsRecoverable: null,
      weeklyLettingIncomePerUnit: null,
      estimatedNetYield: null,
      onSiteRequired: null,
      propertyPurchaseRequired: null,
      ratingScore: null,
      ratingBasis: "招标项目(截止2026-04-17 4PM AEST)，无任何披露数据，无法评分。'Brisbane premier properties'定位暗示体量可能大(>$800K)。需获取Tender Pack后才能评估",
      dataGaps: "要价：由招标确定，非固定价\n所有收入数据：均未披露，需Tender Pack\n合同条款及剩余年限：未知\nLetting / 总套数：未知\nBC薪资：未知\n是否需要Onsite或Office Hours：未知",
      nextAction: "获取Tender Pack; 截止4/17需尽早准备材料",
      dataSource: "Accom Properties (Tender closes Apr 17, 2026 4PM AEST)",
      sourceUrl: "https://accomproperties.com.au/business-display/business-brisbane-city,19103",
      tenderDeadline: "2026-04-17T16:00:00+10:00"
    }
  ];

  // ───────────────────────────────────────────
  // TAB 1: ranking
  // ───────────────────────────────────────────
  var rkSheet = ss.getSheetByName("ranking");
  if (!rkSheet) rkSheet = ss.insertSheet("ranking");
  rkSheet.clear();

  var rkHeaders = [
    "propertyName","location","askingPrice","netIncome","multiplier",
    "contractYearsRemaining","bcSalaryPercent","lettingPoolUnits",
    "weeklyLettingIncomePerUnit","ratingScore","nextAction"
  ];
  var rkRows = [];
  for (var i = 0; i < D.length; i++) {
    var d = D[i];
    rkRows.push([
      d.propertyName, d.location, d.askingPrice, d.netIncome,
      d.multiplier, d.contractYearsRemaining, d.bcSalaryPercent,
      d.lettingPoolUnits, d.weeklyLettingIncomePerUnit,
      d.ratingScore, d.nextAction
    ]);
  }
  rkSheet.getRange(1, 1, 1, rkHeaders.length).setValues([rkHeaders]);
  rkSheet.getRange(2, 1, rkRows.length, rkHeaders.length).setValues(rkRows);
  rkSheet.getRange("A:A").setNumberFormat("$#,##0");
  rkSheet.setFrozenRows(1);

  // Add Data Validation dropdown for filtering
  try {
    var filterRange = rkSheet.getRange(1, 1, rkRows.length + 1, rkHeaders.length);
    filterRange.createFilter();
  } catch (e) {
    Logger.log("Filter error: " + e);
  }

  // Format currency columns
  var priceRange = rkSheet.getRange(2, 3, rkRows.length, 1); // askingPrice
  var niRange    = rkSheet.getRange(2, 4, rkRows.length, 1); // netIncome
  priceRange.setNumberFormat("$#,##0");
  niRange.setNumberFormat("$#,##0");

  // Format score column
  var scoreRange = rkSheet.getRange(2, 10, rkRows.length, 1); // ratingScore
  scoreRange.setNumberFormat("0.0");

  // Column widths
  rkSheet.setColumnWidth(1, 220);  // propertyName
  rkSheet.setColumnWidth(2, 250);  // location
  rkSheet.setColumnWidth(3, 100);  // askingPrice
  rkSheet.setColumnWidth(4, 100);  // netIncome
  rkSheet.setColumnWidth(5, 80);   // multiplier
  rkSheet.setColumnWidth(6, 100);  // contractYearsRemaining
  rkSheet.setColumnWidth(7, 100);  // bcSalaryPercent
  rkSheet.setColumnWidth(8, 100);  // lettingPoolUnits
  rkSheet.setColumnWidth(9, 100);  // weeklyLettingIncomePerUnit
  rkSheet.setColumnWidth(10, 90);  // ratingScore
  rkSheet.setColumnWidth(11, 250); // nextAction

  // ───────────────────────────────────────────
  // TAB 2: raw_data
  // ───────────────────────────────────────────
  var rdSheet = ss.getSheetByName("raw_data");
  if (!rdSheet) rdSheet = ss.insertSheet("raw_data");
  rdSheet.clear();

  var rdHeaders = [
    "id","propertyName","location","askingPrice","netIncome","multiplier",
    "estimatedNetIncome","estimatedMultiplier","contractYearsRemaining",
    "bcSalary","bcSalaryPercent","lettingPoolUnits","totalUnits",
    "externalUnitsRecoverable","weeklyLettingIncomePerUnit",
    "estimatedNetYield","onSiteRequired","propertyPurchaseRequired",
    "ratingScore","ratingBasis","dataGaps","nextAction","dataSource",
    "sourceUrl","tenderDeadline"
  ];
  var rdRows = [];
  for (var j = 0; j < D.length; j++) {
    var d = D[j];
    rdRows.push([
      d.id, d.propertyName, d.location, d.askingPrice, d.netIncome,
      d.multiplier, d.estimatedNetIncome, d.estimatedMultiplier,
      d.contractYearsRemaining, d.bcSalary, d.bcSalaryPercent,
      d.lettingPoolUnits, d.totalUnits, d.externalUnitsRecoverable,
      d.weeklyLettingIncomePerUnit, d.estimatedNetYield,
      d.onSiteRequired, d.propertyPurchaseRequired, d.ratingScore,
      d.ratingBasis, d.dataGaps, d.nextAction, d.dataSource,
      d.sourceUrl, d.tenderDeadline
    ]);
  }
  rdSheet.getRange(1, 1, 1, rdHeaders.length).setValues([rdHeaders]);
  rdSheet.getRange(2, 1, rdRows.length, rdHeaders.length).setValues(rdRows);
  rdSheet.setFrozenRows(1);

  // Format currency columns
  rdSheet.getRange(2, 4, rdRows.length, 1).setNumberFormat("$#,##0");  // askingPrice
  rdSheet.getRange(2, 5, rdRows.length, 1).setNumberFormat("$#,##0");  // netIncome
  rdSheet.getRange(2, 7, rdRows.length, 1).setNumberFormat("$#,##0");  // estimatedNetIncome
  rdSheet.getRange(2, 10, rdRows.length, 1).setNumberFormat("$#,##0"); // bcSalary

  // Column widths for readability
  rdSheet.setColumnWidth(1, 80);   // id
  rdSheet.setColumnWidth(2, 200);  // propertyName
  rdSheet.setColumnWidth(3, 200);  // location
  rdSheet.setColumnWidth(20, 300); // ratingBasis
  rdSheet.setColumnWidth(21, 300); // dataGaps
  rdSheet.setColumnWidth(24, 300); // sourceUrl

  // ───────────────────────────────────────────
  // TAB 3: due_diligence
  // ───────────────────────────────────────────
  var ddSheet = ss.getSheetByName("due_diligence");
  if (!ddSheet) ddSheet = ss.insertSheet("due_diligence");
  ddSheet.clear();

  var ddHeaders = ["propertyName", "dataGaps", "nextAction", "sourceUrl"];
  var ddRows = [];
  for (var k = 0; k < D.length; k++) {
    var d = D[k];
    ddRows.push([d.propertyName, d.dataGaps, d.nextAction, d.sourceUrl]);
  }
  ddSheet.getRange(1, 1, 1, ddHeaders.length).setValues([ddHeaders]);
  ddSheet.getRange(2, 1, ddRows.length, ddHeaders.length).setValues(ddRows);
  ddSheet.setFrozenRows(1);

  // Column widths
  ddSheet.setColumnWidth(1, 220); // propertyName
  ddSheet.setColumnWidth(2, 350); // dataGaps
  ddSheet.setColumnWidth(3, 300); // nextAction
  ddSheet.setColumnWidth(4, 300); // sourceUrl

  // ───────────────────────────────────────────
  // Conditional Formatting on ranking sheet
  // ───────────────────────────────────────────

  var rules = [];

  // Rule 1: bcSalaryPercent > 80 → Red
  var rl1 = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThan(80)
    .setBackground("#fce8e6")
    .setFontColor("#d93025")
    .setRanges([rkSheet.getRange(2, 7, rkRows.length, 1)])
    .build();
  rules.push(rl1);

  // Rule 2: bcSalaryPercent 60-70 → Green
  var rl2 = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberBetween(60, 70)
    .setBackground("#e6f4ea")
    .setFontColor("#1b9e77")
    .setRanges([rkSheet.getRange(2, 7, rkRows.length, 1)])
    .build();
  rules.push(rl2);

  // Rule 3: multiplier ≤ 5 → Green
  var rl3 = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberLessThanOrEqualTo(5)
    .setBackground("#e6f4ea")
    .setFontColor("#1b9e77")
    .setRanges([rkSheet.getRange(2, 5, rkRows.length, 1)])
    .build();
  rules.push(rl3);

  // Rule 4: weeklyLettingIncomePerUnit < 40 → Red
  var rl4 = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberLessThan(40)
    .setBackground("#fce8e6")
    .setFontColor("#d93025")
    .setRanges([rkSheet.getRange(2, 9, rkRows.length, 1)])
    .build();
  rules.push(rl4);

  // Rule 5: ratingScore ≥ 3.5 → Green
  var rl5 = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThanOrEqualTo(3.5)
    .setBackground("#e6f4ea")
    .setFontColor("#1b9e77")
    .setRanges([rkSheet.getRange(2, 10, rkRows.length, 1)])
    .build();
  rules.push(rl5);

  // Rule 6: ratingScore < 2.5 → Red
  var rl6 = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberLessThan(2.5)
    .setBackground("#fce8e6")
    .setFontColor("#d93025")
    .setRanges([rkSheet.getRange(2, 10, rkRows.length, 1)])
    .build();
  rules.push(rl6);

  rkSheet.setConditionalFormatRules(rules);

  // ───────────────────────────────────────────
  // Sort ranking by ratingScore descending
  // ───────────────────────────────────────────
  var dataRange = rkSheet.getRange(1, 1, rkRows.length + 1, rkHeaders.length);
  // Skip header row for sorting (range row 2 to end)
  var sortRange = rkSheet.getRange(2, 1, rkRows.length, rkHeaders.length);
  sortRange.sort([{column: 10, ascending: false}]); // sort by ratingScore col J (10)

  // ───────────────────────────────────────────
  // Delete temp sheet if created
  // ───────────────────────────────────────────
  var tempSheet = ss.getSheetByName("__temp__");
  if (tempSheet) {
    ss.deleteSheet(tempSheet);
  }

  // ───────────────────────────────────────────
  // Activate ranking sheet
  // ───────────────────────────────────────────
  ss.setActiveSheet(rkSheet);

  Browser.msgBox(
    "✅ Dashboard Created!\n\n" +
    "Sheets created:\n" +
    "  1. ranking - Core metrics with conditional formatting\n" +
    "  2. raw_data - All 25 columns of full data\n" +
    "  3. due_diligence - Data gaps, next actions, source URLs\n\n" +
    "Conditional formatting applied:\n" +
    "  🔴 BC% > 80 | Multiplier > 5 | $/wk < 40\n" +
    "  🟢 BC% 60-70 | Multiplier ≤ 5 | Rating ≥ 3.5\n\n" +
    "Properties: " + D.length + " | Sorted by rating score"
  );
}
