# PMR Google Sheets 导入指南

## 1. 创建 Google Sheet

1. 打开 https://sheets.new 创建一个新的 Google Sheet
2. 建议命名为 **PMR Investment Tracker**

## 2. 新建两个工作表

在底部标签栏：

- **右键默认标签** → 重命名为 `raw_json`
- **点击 +** 创建第二个标签 → 重命名为 `pmr_table`

> ⚠️ 标签名必须完全匹配 `raw_json` 和 `pmr_table`（区分大小写）

## 3. 粘贴 JSON 数据

1. 打开文件 `pmr-data-latest.json`（在工作区中）
2. 在编辑器中 **全选复制全部内容**（从第一个 `[` 到最后一个 `]`）
3. 回到 Google Sheet → 选中 `raw_json` 工作表 → **点击单元格 A1**
4. **粘贴** — 确保整个 JSON 数组文本出现在 A1 中
   - 如果粘贴后内容被分割到多个单元格，说明粘贴方式不对，改用 **双击 A1 后粘贴**

## 4. 安装 Google Apps Script

1. 在 Google Sheet 顶部菜单 → **Extensions（扩展程序） > Apps Script**
2. 在代码编辑器中 **删除默认的 `function myFunction() {}` 代码**
3. **粘贴** `google-sheets-import.gs` 的全部内容
4. 点击顶部 **💾 Save（保存）** 按钮
5. 将项目命名为 **PMR Importer**

## 5. 运行脚本

1. 在 Apps Script 窗口顶部工具栏，确认下拉菜单选中了 **`pmrImport`**
2. 点击 **▶ Run（运行）**
3. 首次运行时 Google 会要求**授权**：
   - 点击 **Review permissions（审查权限）**
   - 选择你的 Google 账号
   - 如果出现 ⚠️ "Google hasn't verified this app" 警告 → 点击 **Advanced（高级）** → **Go to PMR Importer (unsafe)**
   - 点击 **Allow（允许）**
4. 回到 Google Sheet，`pmr_table` 工作表将自动生成

## 6. 每次更新数据

当收到新的 PMR JSON 数据时：

1. 选中 `raw_json` → A1 → 粘贴新的 JSON
2. Apps Script → `pmrImport` → ▶ Run
3. `pmr_table` 将自动刷新（覆盖旧数据）

## 7. 推荐操作

### 7.1 筛选器
在 `pmr_table` 中：
- 选中第 1 行标题（`Ctrl+A` 或全选）
- **Data（数据） > Create a filter（创建筛选器）**
- 点击列标题旁的筛选图标，可按价格、评分、BC%等筛选

### 7.2 排序
- 选中全部数据（含标题）
- **Data（数据） > Sort range（对范围排序） > Advanced range sorting options**
- 选 **Rating Score** → **Descending（降序）** → Sort

### 7.3 条件格式（推荐规则）

选中 `pmr_table` 全部数据后：
**Format（格式） > Conditional formatting（条件格式）**

| 规则 | 范围 | 公式/条件 | 格式 |
|------|------|-----------|------|
| BC% > 80 | K:K（BC Salary %列） | 数值 > 80 | 🔴 红色背景 |
| BC% 60-80 | K:K | 数值在 60-80 之间 | 🟢 绿色背景 |
| Multiplier ≤ 5 | F:F（Multiplier列） | 数值 ≤ 5 | 🟢 绿色背景 |
| Multiplier > 8.5 | F:F | 数值 > 8.5 | 🔴 红色背景 |
| Rating < 2.5 | T:T（Rating Score列） | 数值 < 2.5 | 🔴 红色背景 |
| Rating ≥ 3.5 | T:T | 数值 ≥ 3.5 | 🟢 绿色背景 |
| $/Wk/Unit < 40 | P:P | 数值 < 40 | 🔴 红色背景 |

### 7.4 冻结标题行
- 选中第 2 行
- **View（视图） > Freeze（冻结） > 1 row**

### 7.5 隐藏不常用的列
右键列标题 → **Hide column** → 推荐隐藏：
- D (ID) — 内部标识
- R (External Units Recoverable)
- S (Estimated Net Yield)
- W (Rating Basis) — 太长，可放备注列
- X (Data Gaps) — JSON 中已保留
- Z (Data Source)

## 8. 新增物业

当发现新的 PMR 挂牌时：
1. 手动在 `pmr_table` 末尾添加一行
2. 同时更新 `pmr-data-latest.json`
3. 下次重新导入时会覆盖手动修改，所以建议**先在 JSON 中添加，再运行脚本**
