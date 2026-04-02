# PMR Google Sheets — 列规划

## 推荐保留列（可见）

| 列号 | 字段 | 用途 |
|------|------|------|
| B | ID | 内部标识 |
| C | Property Name | 物业名称 |
| D | Location | 位置 |
| E | Asking Price | 要价 |
| F | Net Income | 净收入 |
| G | Multiplier | 倍数 |
| H | Est. Net Income | 估算净收入（未确认时） |
| I | Est. Multiplier | 估算倍数（未确认时） |
| J | Contract Years Remaining | 合同剩余年限 |
| K | BC Salary % | 薪资占比（核心风控指标） |
| L | Letting Pool Units | 出租池数量 |
| M | Total Units | 总套数 |
| N | $/Wk/Unit | 每单元每周佣金 |
| O | Est. Net Yield | 估净收益率 |
| Q | Rating Score | 综合评分 |
| R | Next Action | 下一步 |

## 推荐隐藏列（可展开查看）

| 列号 | 字段 | 原因 |
|------|------|------|
| A | # | Sheets 行号已可见，此列冗余 |
| P | On-Site Required | 当前全部为 false |
| S | ratingBasis | 文本太长，可放备注区 |
| T | dataGaps | 文本太长，可展开时查看 |
| U | nextAction（原始）| 列 R 已保留 |
| V | Data Source | 仅用于溯源 |
| W | Source URL | 可放超链接 |
| X | Tender Deadline | 仅投标项目使用 |

## 推荐公式列

在 `pmr_table` 右侧新增以下列（建议从 Z 列开始）：

### Z: DataCompleteness（数据完整度 %）

```
=COUNTIF(E2:O2, "<>")/9
```
- 统计 E-O 列中 9 个关键字段有多少非空
- 格式化为百分比，≥60% 标绿

### AA: CashFlowFlag（现金流标记）

```
=IF(OR(F2="", K2=""), "未知", IF(K2>80, "高风险", IF(K2<70, "可投资", "关注")))
```

### AB: VerifyPriority（尽调优先级）

```
=IF(Q2>=4, "低", IF(Q2>=3.5, "中", IF(Q2>=2.5, "高", "紧急")))
```

### AC: InvestmentGrade（投资分级）

```
=IF(AND(K2>=60, K2<=70, G2>=4.5, G2<=5.5), "A", IF(AND(K2>=60, F2<>""), "B", "C"))
```

## 推荐条件格式规则

### 按列设置

| 列 | 条件 | 格式 |
|----|------|------|
| K (BC Salary %) | >80 | 🔴 红色背景 |
| K (BC Salary %) | 60–70 | 🟢 绿色背景 |
| G (Multiplier) | ≤ 5 | 🟢 绿色背景 |
| G (Multiplier) | > 6.5 | 🔴 红色背景 |
| N ($/Wk/Unit) | < 40 | 🔴 红色背景 |
| Q (Rating Score) | ≥ 3.5 | 🟢 绿色背景 |
| Q (Rating Score) | < 2.5 | 🔴 红色背景 |
| AB (VerifyPriority) | ="紧急" | 🔴 红色背景 |
| AB (VerifyPriority) | "高" | 🟡 橙色背景 |

### 整行高亮规则（选中整行数据范围）

- 选中 `A2:X100` → Conditional formatting
- **自定义公式**: `=$K2>80` → 🔴 红色背景（BC% 过高 = 整行红色）
- **自定义公式**: `=$Q2>=4` → 🟢 绿色背景（评分≥4 = 整行绿色）

## 建议布局

```
[A-W] │ 原始数据列（24 列）
[X]   │ DataCompleteness (公式)
[Y]   │ CashFlowFlag     (公式)
[Z]   │ VerifyPriority   (公式)
[AA]  │ InvestmentGrade  (公式)
```

> 建议新建 "Dashboard" 工作表，使用 `=QUERY()` 或 `=FILTER()` 从 pmr_table 中提取 Top 候选。
