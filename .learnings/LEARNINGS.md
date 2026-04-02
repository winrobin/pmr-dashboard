# Learnings - PMR Analysis Improvements

## [LRN-20260331-001] critical-v3-analysis-flaws

**Logged**: 2026-03-31T12:20:00+10:00
**Priority**: high
**Status**: resolved
**Area**: analysis

### Summary
V3 PMR analysis missed critical red flags due to lack of BC salary percentage and per-unit letting income calculations.

### Details
User review of V3 (pmr-data-v3.json + pmr-report-v3.html) identified several severe deficiencies:

1. **Silver Quays (KP-001)**: BC salary $129,395 out of net income $138,231 = 93.6%. Letting pool 5 units → $8,836 annual letting income = $34/week/unit. This is abnormally low (Brisbane normal: $60-85/week/unit). The business is essentially a caretaker job, not a PMR investment. V3 incorrectly described it as "very stable" and ranked it #1.

2. **Missing BC% analysis**: No field to calculate and display BC salary as percentage of net income. Normal PMR range: 60-70%. >80% indicates caretaker-dependent model.

3. **Missing per-unit letting commission**: No calculation of `(netIncome - bcSalary) / lettingPoolUnits / 52` to assess true letting revenue quality.

4. **Chermside/Lutwyche (CH-001)**: Had "$178K net income" mentioned in ratingBasis but multiplier was null. Should include `estimatedMultiplier` field with clear disclaimer.

5. **Ranking was inverted**: High multiplier (5.0x, 6.17x) appeared attractive, but without BC% analysis, the true risk (93.6% BC dependency) was hidden.

### Suggested Action
For V4:

- Add derived fields: `bcSalaryPercent`, `weeklyLettingIncomePerUnit`
- Color-code: BC% 🟢60-70% 🟡70-80% 🔴>80%; commission 🟢$60-85/wk 🟡$40-60/wk 🔴<$40/wk
- Re-rank properties: The Gap (BC 61.5% healthy) should be #1, Silver Quays (BC 93.6% dangerous) should be downgraded to #5 or lower
- Add `estimatedMultiplier` to CH-001 with clear "unverified" note
- Add `rw` (risk warnings) array to JSON for HTML to render as red warning bars
- Include `totalUnits` where known to calculate `lettingPoolPercent` (e.g., Silver Quays 5/49=10.2%)
- HTML comparison table must show these new metrics

### Metadata
- Source: user_feedback
- Related Files: pmr-data-v3.json, pmr-report-v3.html, pmr-data-v4.json, pmr-report-v4.html
- Tags: correction, quality_gap, pfm, risk_analysis
- See Also: (promote to SOUL.md if recurring)
- Pattern-Key: pfm.add-bc-percentage-analysis
- Recurrence-Count: 1
- First-Seen: 2026-03-31
- Last-Seen: 2026-03-31

### Resolution
- 2026-03-31: Created V4 JSON with bcSalaryPercent, weeklyLettingIncomePerUnit, estimatedMultiplier (CH-001)
- Re-ranked: The Gap #1 (4.2), West End #2 (3.9), Chermside #3 (3.5), Brisbane City #4 (2.5), Silver Quays #5 (2.0)
- Added risk warning arrays (rw) for Silver Quays
- HTML now color-codes BC% and commission levels
- Comparison table includes all derived metrics

---

## [LRN-20260331-002] json-schema-file-mismatch

**Logged**: 2026-03-31T12:25:00+10:00
**Priority**: medium
**Status**: resolved
**Area**: config

### Summary
HTML report referenced incorrect JSON filename (pmr-data-v3.json vs actual pmr-data-v3-2.json), causing export/load failures.

### Details
User downloaded and opened pmr-report-v3.html, which contained a footer reference to `pmr-data-v3.json`. The actual JSON file used/created was `pmr-data-v3-2.json` (likely from a prior iteration). This mismatch means any "export" button or client-side script trying to load the JSON would fail with 404.

The issue arose because:
- Multiple versions of files created during iterative development
- HTML hardcoded filename instead of deriving from script context
- No single source of truth for the paired JSON filename

### Suggested Action
For future HTML reports:
- Embed JSON data directly in the HTML as a `<script>` variable to eliminate separate file dependency for viewing
- If separate JSON file is needed, use a consistent filename pattern (e.g., `pmr-report-v<major>.html` pairs with `pmr-data-v<major>.json`)
- Or, add a configuration comment in HTML footer: `Data source: pmr-data-v3.json` but ensure consistency

In V4:
- HTML is self-contained with JSON embedded in JavaScript (no external fetch needed for viewing)
- If external JSON is required, name both files with same version string

### Metadata
- Source: error
- Related Files: pmr-report-v3.html, pmr-data-v3-2.json, pmr-report-v4.html, pmr-data-v4.json
- Tags: bug, file_management, ux
- See Also: (none yet)
- Pattern-Key: report.ensure-filename-pair-consistency
- Recurrence-Count: 1
- First-Seen: 2026-03-31
- Last-Seen: 2026-03-31

### Resolution
- V4 HTML embeds all data in JavaScript array `P=[]` — no external JSON needed for viewing
- JSON file `pmr-data-v4.json` remains available for export/analysis but is not required for HTML rendering
- Filenames now consistent: `pmr-report-v4.html` and `pmr-data-v4.json`

---

## [LRN-20260331-003] ch-001-estimated-multiplier-missing

**Logged**: 2026-03-31T12:25:00+10:00
**Priority**: medium
**Status**: resolved
**Area**: data_quality

### Summary
CH-001 (Chermside/Lutwyche) had unverified net income figures mentioned in ratingBasis but multiplier was null. Lacked `estimatedMultiplier` field to capture unofficial data with proper disclaimer.

### Details
Original V3 JSON for CH-001:
```json
{
  "netIncome": null,
  "multiplier": null,
  "ratingBasis": "... $178K 为网传数据..."
}
```

This creates two problems:
1. The multiplier cannot be calculated, obscuring the potential value (if $178K is true, multiplier = 652000/178000 ≈ 3.66x — very attractive)
2. The information exists in free text but is not machine-parseable for sorting/comparison

User expects structured fields: `estimatedMultiplier` and `estimatedMultiplierNote` to capture unverified numbers separately from official data.

### Suggested Action
Add these fields to JSON schema:
- `estimatedMultiplier` (number|null)
- `estimatedMultiplierNote` (string) explaining source and disclaimer
- Similarly consider `estimatedNetIncome` if source exists

In V4:
```json
{
  "estimatedMultiplier": 3.66,
  "estimatedMultiplierNote": "基于网传$178K 净收入估算，仅供参考"
}
```

### Metadata
- Source: user_feedback
- Related Files: pmr-data-v4.json
- Tags: data_quality, schema, pfm
- Pattern-Key: data.add-estimated-fields-with-disclaimers
- Recurrence-Count: 1
- First-Seen: 2026-03-31
- Last-Seen: 2026-03-31

### Resolution
- V4 JSON includes estimatedMultiplier for CH-001 with clear note
- Documented in ratingBasis that multiplier is "估3.66x仅供参考"
- Suggest adding same pattern for netIncome if sources exist in future

---

## [FEAT-20260331-001] pfm-risk-warning-array

**Logged**: 2026-03-31T12:30:00+10:00
**Priority**: medium
**Status**: resolved
**Area**: frontend

### Summary
User requested explicit risk warning fields to be displayed prominently in HTML reports, rather than burying red flags inside ratingBasis text.

### Details
For Silver Quays, the severity of BC% = 93.6% was lost in the ratingBasis paragraph. The HTML needed to make it impossible to miss.

User wanted:
- Separate `rw` (risk warnings) array in JSON
- Displayed as red alert bars (🚨) before ratingBasis in card layout

### Suggested Action
Add field to each property:
```json
"rw": [
  "🚨 BC 93.6% 远超 60-70% 健康区间 —— 本质是 caretaker 工作而非 PMR",
  "🚨 每单元每周仅 $34 佣金极低（布里斯班正常 $60-85）"
]
```

HTML renders as visible warning blocks if array non-empty.

### Metadata
- Source: user_feedback
- Related Files: pmr-data-v4.json, pmr-report-v4.html
- Tags: ux, risk_display, pfm
- Area: frontend
- Frequency: recurring
- Related Features: color-coded metrics, data completeness

### Resolution
- Added `rw` field to V4 JSON
- Rendered in HTML with red background and 🚨 icon
- Placed above ratingBasis but below core metrics

---

## [LRN-20260331-004] simplify-dedup-field-count

**Logged**: 2026-03-31T12:35:00+10:00
**Priority**: low
**Status**: pending
**Area**: config

### Summary
Data completeness bar uses hardcoded field count (9 or 8) and field list; hard to maintain when schema evolves.

### Details
JavaScript in HTML defines:
```js
var TF=9, K=["p","ni","m","c","bc","bcp","pu","ey","r"];
function co(x){var c=0;K.forEach(...) return c}
```

If we add new important fields (e.g., `wli`, `rw`), the completeness % becomes accurate only if we remember to update `TF` and `K`.

Better approach:
- Compute completeness based on a canonical list of KEY fields that matter for investment decisions
- Or derive completeness from JSON schema if available
- Or calculate `c` as count of non-null values in the object (but null vs missing differs)

### Suggested Action
Refactor to:
```js
var KEY_FIELDS = ['price','netIncome','multiplier','contractYearsRemaining','bcSalary','bcSalaryPercent','lettingPoolUnits','weeklyLettingIncomePerUnit','ratingScore'];
function completeness(obj) {
  return KEY_FIELDS.reduce((c,k)=> c + (obj[k]!==null?1:0), 0);
}
var F = KEY_FIELDS.length;
```

Keep KEY_FIELDS in sync with data schema.

### Metadata
- Source: self_improvement
- Related Files: pmr-report-v4.html
- Tags: maintainability, simplify
- Pattern-Key: simplify.dedup-field-count
- Recurrence-Count: 1
- First-Seen: 2026-03-31
- Last-Seen: 2026-03-31

### Status
pending - needs refactor in next version

---

## [LRN-20260331-005] no-javascript-on-iphone-safari-local-files

**Logged**: 2026-03-31T15:02:00+10:00
**Priority**: **CRITICAL**
**Status**: resolved
**Area**: delivery

### Summary
**Spent 30+ turns failing because JS doesn't execute in iPhone Safari on local HTML files.** The user saw title + table headers (static HTML) but all cards/data (JS-rendered) were blank.

### Details
The user requested V4 → V5 report upgrades. Multiple versions were made:
1. V5 with JS embedded — showed no cards on iPhone
2. Simplified JS versions — still no cards
3. User said "I can see The Gap card but data is wrong" — data was correct per my files but iPhone Safari was likely rendering a partially cached/corrupted version
4. User switched to MacBook — showed garbled Unicode
5. Switched to pure ASCII — user said "I only see title and comparison table text, no data"
6. Multiple DOM/JS versions — still no data on iPhone

Root cause: **JavaScript does not execute when opening local `file://` HTML files in iPhone Safari** (iOS 15+ security restrictions). Every JS-based version silently failed — the user saw a blank page with only the static HTML elements that were outside `<script>` tags.

**Wasted 30+ turns** because:
- I assumed JS was working because the file was valid HTML
- I kept rewriting JS logic instead of verifying it actually executed
- I didn't test with a "zero JS" version until the user's 5th complaint
- I sent conflicting diagnoses ("JS string concat broken by Telegram", "Unicode encoding issue") when the REAL issue was JS not running at all

### What Went Wrong
- **Assumed without verifying**: Never sent a "Hello World" test with console.log to confirm JS execution
- **Over-engineered**: Kept iterating on complex JS when the real solution was "use zero JS"
- **Didn't ask the right question**: Should have asked "is the JS running at all?" from turn 1
- **Sent too many versions**: Created confusion with multiple concurrent files
- **Ignored user's actual evidence**: User's screenshot showed static HTML working but no dynamic content — this was the clearest signal of "JS not executing"

### Solution
Pure static HTML — no `<script>` tags at all. All data hardcoded directly into HTML elements. Works immediately on all devices.

### Rules Going Forward
- **Rule 1**: When user says "I can see the page but no data", first suspect JS not executing. Send a zero-JS test version immediately.
- **Rule 2**: For iPhone/iPad delivery of HTML files to users, **always default to pure static HTML**. Only use JS if explicitly needed (filters, interactions).
- **Rule 3**: Never send multiple versions in rapid succession. Send one, wait for feedback, diagnose from what the user actually sees.
- **Rule 4**: When user reports "blank" or "empty", ask for a screenshot immediately — the screenshot at turn 31 would have been enough.

### Metadata
- Source: user_feedback
- Related Files: pmr-report-v4.html, pmr-report-v5.html (multiple iterations), pmr-report-iphone.html
- Tags: **critical_lesson**, ios, safari, javascript, html_delivery
- Pattern-Key: delivery.zero-js-static-html-for-ios
- Recurrence-Count: 1
- First-Seen: 2026-03-31
- Last-Seen: 2026-03-31

---

## [LRN-20260331-006] stop-guessing-diagnose-first

**Logged**: 2026-03-31T15:02:00+10:00
**Priority**: **CRITICAL**
**Status**: pending (behavioral)
**Area**: workflow

### Summary
Spent 30+ turns sending incorrect fixes because I kept guessing the root cause instead of running proper diagnostics.

### What I Should Have Done
1. User said "can't see content" → ask for screenshot (turn 2)
2. Screenshot shows static HTML but no dynamic content → diagnose "JS not executing" (turn 3)
3. Send minimal test: `<p>JS works: <span id="x"></span></p><script>document.getElementById('x').textContent='YES'</script>` (turn 3)
4. If test fails on iPhone Safari → switch to pure static HTML (turn 4)
5. **Done in 4 turns instead of 30+**

### Rules Going Forward
- **Diagnose before fixing**: Don't send 5 different "fixes" — understand the problem first
- **Use screenshots as evidence**: User screenshots are the primary diagnostic tool, not file content inspection
- **Static first, interactive later**: If delivery channel (iOS Safari) is known to be restrictive, default to static
- **Send one version, wait**: Don't queue multiple versions — it creates confusion about which is the actual fix

### Metadata
- Source: self_improvement
- Tags: workflow, debugging, user_experience
- Pattern-Key: workflow.diagnose-before-fixing
- Recurrence-Count: 1

---

## [ERR-20260331-001] composio-openclaw-plugin-fails-to-load

**Logged**: 2026-03-31T16:50:00+10:00
**Priority**: high
**Status**: unresolved
**Area**: config

### Summary
Composio OpenClaw plugin (@composio/openclaw-plugin v0.0.9) cannot be loaded as a persistent plugin. Every install succeeds temporarily but the plugin is not found on next config read.

### Error
- `openclaw plugins inspect composio` → "Plugin not found: composio"
- Config warning on every CLI call: `plugins.entries.composio: plugin composio: plugin id mismatch (manifest uses "composio", entry hints "openclaw-plugin")`
- Config also warns: `plugins.entries.composio: plugin not found: composio (stale config entry ignored)`
- Extension directory `/Users/oc/.openclaw/extensions/composio/` exists immediately after install but is GONE after `openclaw gateway restart`

### Context
- OpenClaw version: 2026.3.24
- Plugin installed via: `openclaw plugins install @composio/openclaw-plugin`
- Consumer key: `ck_oo-Q1YynR8cYXQ0NcPNr` set correctly
- Plugin tools registered during install (7 tools) but disappear on restart
- Root cause appears to be: plugin manifest ID "composio" ≠ npm package name "@composio/openclaw-plugin", causing config validation failures on every restart

### Suggested Fix
- This is an OpenClaw plugin loader bug — cannot fix from agent side
- Workaround: Use the pre-installed Composio tools via system prompt injection instead of plugin (they're available as native tools)
- Alternative: File bug report for OpenClaw plugin ID mismatch handling

### Metadata
- Source: error
- Reproducible: yes (100%)
- Related Files: `/Users/oc/.openclaw/openclaw.json`, `/Users/oc/.openclaw/extensions/composio/`
- Pattern-Key: harden.openclaw-plugin-id-mismatch
- Recurrence-Count: 1
- First-Seen: 2026-03-31
- Last-Seen: 2026-03-31

## [LRN-20260331-007] html-javascript-not-executing-on-mobile-ios

**Logged**: 2026-03-31T16:50:00+10:00
**Priority**: critical
**Status**: resolved
**Area**: delivery

### Summary
All JS-based HTML deliveries to iPhone/iPad via Telegram were silently failing — user saw only static HTML (title, headers) while all JS-rendered content was blank. Wasted 40+ turns before realizing JS didn't execute at all.

### Details
Multiple JS delivery approaches failed on iPhone Safari when opening .html files from Telegram:
1. JS string concatenation → "didn't render"
2. DOM API version → "didn't render"
3. Pure static HTML (zero JS) → worked immediately on first try

The user sent a screenshot showing title + table headers visible but no data — this was the clearest signal that JS wasn't executing, but I misdiagnosed it as:
- String concatenation bug
- Unicode encoding issue
- Telegram file size limit
- Quote escaping

### Root Cause
iPhone Safari does not execute `<script>` tags when opening `file://` protocol HTML files. This is a known iOS security restriction.

### Suggested Action (Promoted)
**Promoted to TOOLS.md**: For HTML file delivery to iPhone/iPad users, ALWAYS use pure static HTML. No JavaScript. Zero `<script>` tags.

### Metadata
- Source: user_feedback
- Related Files: pmr-report-v4.html, pmr-report-v5.html, pmr-report-latest.html
- Tags: ios, safari, javascript, html-delivery, mobile
- Pattern-Key: delivery.pure-static-html-for-ios
- Recurrence-Count: 1
- First-Seen: 2026-03-31
- Last-Seen: 2026-03-31

---

