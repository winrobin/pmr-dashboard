import re

fpath = '/Users/oc/.openclaw/workspace/index.html'
with open(fpath, 'r', encoding='utf-8') as f:
    html = f.read()

# Bilingual replacements for rw and bx divs
rw_map = [
    ['✅ BC 61.5% ideal | 23yr contract | $68/wk normal | Minimal no Gate', 'BC 61.5%理想 | 23年合同 | $68/周正常'],
    ['⚠️ Total units unknown | 12 ext unit recovery needs written BC confirmation', '总套数未知 | 12外部单元收回需确认'],
    ['✅ BC 61.1% health | CPI annual | New building low maint', 'BC61.1%健康 | CPI递增 | 楼龄新'],
    ['⚠️ Pool completely undisclosed = main risk', 'Pool数据全无 — 主要风险'],
    ['✅ BC 66.6% ideal | 4.05x excellent | Residency $610/wk ($31.8K/yr extra)', 'BC66.6%理想 | 4.05x极佳 | 住宅$610/周'],
    ['⚠️ Pool + contract unverified', 'Pool/合同待核实'],
    ['⚠️ Blue-chip Teneriffe near CBD+Riverwalk | All data missing | $1.36M over budget', 'Teneriffe蓝钻地段 | 全数据缺失 | 超预算'],
    ['✅ BC 57.5% health | $431K net | 52Pool | Multiple top-up history', 'BC57.5%健康 | $431K | 52Pool'],
    ['⚠️ $2.9M over budget | 8yr contract short | 150-unit complex heavy', '$2.9M超预算 | 8年合同 | 150单元'],
    ['✅ BC 52% very healthy | 21yr | 48% from letting | Holiday+Permanent', 'BC52%极健 | 21年 | 48%租赁'],
    ['✅ No onsite | No office hrs | Manager unit $850K extra', '无需onsite | 无办公 | 经理unit $850K'],
    ['⚠️ $1.89M over | 7.87x high', '$1.89M超预算 | 7.87x偏高'],
    ['✅ 16/28=57% Pool ratio excellent | 18yr contract', '16/28=57%Pool比例极佳 | 18年合同'],
    ['⚠️ Net/BC unknown | $1.55M over', '净利/BC未知 | $1.55M超预算'],
    ['Excellent fundamentals but too big for now. Contact Resort Brokers MR009117.', '基本面极佳但现在太大。联系MR009117。'],
    ['BEST in Tier 2+. When budget expands to $1.5M-$2M, pick this first.', 'Tier2+最佳。预算扩展时首选。'],
    ['GC. Net $80K, Remun $71K, Pool 5. BC 89.5% borderline caretaker. 1.6M incl. estate. Over Tier1.', 'GC。Net $80K, Pool 5。BC 89.5%接近caretaker。超Tier1。'],
    ['Service provider agreement + letting agent authority. No unit/re contract cost. Tender closes Apr 17 4PM. All data undisclosed.', '服务协议+租赁代理。不需购unit。截止4/17。无数据。'],
    ['Needs due diligence on all operating data. No detailed info yet.', '需尽调所有运营数据。目前无详细信息。'],
]

bx_map = [
    ['BC83.7% borderline + $24/wk very low. 2 adjoining complexes. Pool 8/42=19% has growth potential. 16yr contract.', 'BC83.7% + $24/周极低。Pool 8/42=19%有增长。16年合同。'],
    ['BC100% pure caretaker, no letting, 21 units 20 owner-occupied. Only as portfolio add-on.', 'BC100%纯caretaker，无letting。仅portfolio附加。'],
    ['Net $257K healthy, 5.25x OK, blue-chip Bulimba. But total $2.14M + BC unknown + Pool unknown.', '净利$257K健康，5.25x可以。但总投入$2.14M。'],
    ['Clontarf (Moreton Bay) MR. Needs due diligence on BC/Pool/Contract/Net.', 'Clontarf MR。需尽调BC/Pool/合同。'],
    ['No onsite | No office hrs | Manager unit $850K extra', 'No onsite | no office hrs | $850K extra'],
    ['$1.89M over | 7.87x high', '$1.89M超预算 | 7.87x偏高'],
]

count = 0
for en, zh in rw_map + bx_map:
    # Find div with this exact text
    pat = '><span class="c-en">' + en + '</span>'
    if pat in html:
        continue  # Already bilingual
    old_div = '><' + en + '<'
    if old_div in html:
        new_div = '><span class="c-en">' + en + '</span><span class="c-zh" style="display:none">' + zh + '</span><'
        html = html.replace(old_div, new_div, 1)
        count += 1
        print(f"OK: {en[:40]}")
    else:
        print(f"MISS: {en[:40]}")

print(f"\nTotal: {count}")

with open(fpath, 'w', encoding='utf-8') as f:
    f.write(html)
