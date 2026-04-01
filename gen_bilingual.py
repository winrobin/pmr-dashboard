#!/usr/bin/env python3
# Generate bilingual PMR Daily Brief HTML

html = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PMR Daily Brief</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0b0f;color:#fff;font-family:-apple-system,sans-serif;padding-bottom:20px}
.lng-btn{position:fixed;top:8px;right:8px;z-index:200;background:#1d4ed8;color:#fff;border:none;font-size:11px;font-weight:bold;padding:7px 12px;border-radius:6px;cursor:pointer;opacity:0.95}
.lng-btn:hover{opacity:1}
.hd{background:#111827;padding:14px 10px;border-bottom:2px solid #1e2635;text-align:center;padding-right:70px}
.hd h1{font-size:14px;margin:0 0 4px 0}
.s{font-size:10px;color:#6b7b8d;margin-top:2px}
.tabs{display:flex;border-bottom:1px solid #232d3d;position:sticky;top:0;z-index:10;background:#111827;flex-wrap:wrap}
.tab{flex:1;min-width:60px;padding:10px 4px;text-align:center;font-size:10px;font-weight:bold;color:#6b7b8d;cursor:pointer;border-bottom:3px solid transparent}
.tab.act{border-bottom-color:#4a9eff;color:#4a9eff}
.tp{display:none;padding:8px}.tp.act{display:block}
.nb{padding:8px}
.c{background:#141922;border-radius:8px;margin-bottom:8px;border:1px solid #232d3d}
.ch{display:flex;align-items:center;padding:8px;gap:6px}
.rk{font-weight:bold;font-size:10px;padding:2px 5px;border-radius:7px;color:#fff}
.r1{background:#f59e0b}.r2{background:#6b7b8d}.r3{background:#b45309}.r5{background:#ef4444}
.nm{font-size:13px;font-weight:bold;flex:1}
.lk{background:#1d4ed8;color:#fff;font-size:10px;padding:2px 4px;border-radius:3px;text-decoration:none}
.badge{font-size:8px;padding:1px 4px;border-radius:3px;margin-left:4px;font-weight:bold}
.badge.g{background:rgba(34,197,94,.15);color:#22c55e}
.badge.r{background:rgba(239,68,68,.15);color:#ef4444}
.badge.y{background:rgba(251,191,36,.15);color:#fbbf24}
.badge.b{background:rgba(96,165,250,.15);color:#60a5fa}
.pr{font-size:13px;color:#4a9eff;font-weight:bold;padding:2px 8px 0;text-align:center}
.mg{display:grid;grid-template-columns:repeat(6,1fr);gap:3px;padding:0 8px;margin:4px 0}
.mi{background:#0e1117;border-radius:4px;padding:4px 2px;text-align:center}
.mi .v{font-size:10px;font-weight:bold}.g{color:#22c55e}.y{color:#fbbf24}.r{color:#ef4444}.n{color:#4b5563}
.mi .l{font-size:6px;color:#6b7b8d;text-transform:uppercase}
.bx{font-size:10px;color:#aaa;background:#0e1117;padding:4px 8px;margin:4px;border-left:2px solid #f59e0b;line-height:1.4}
.ab{font-size:10px;color:#c9d1d9;background:rgba(37,99,235,.1);border-left:2px solid #2563eb;padding:3px 8px;margin:4px 8px 0}
.ab b{color:#60a5fa}
.rw{font-size:9px;color:#f87171;padding:0 8px;margin-bottom:2px}
.rw.g{color:#22c55e}
.tw{overflow-x:auto;padding-bottom:3px;margin:0 8px}
.t{width:100%;border-collapse:collapse;font-size:9px;min-width:480px}
.t th{background:#1a1f2e;padding:3px 1px;text-align:center;color:#666}
.t td{padding:3px 1px;text-align:center;border-bottom:1px solid #191919}
.t td:first-child{text-align:left;font-weight:600;color:#fff}
.ft{text-align:center;padding:12px 6px;color:#4b5563;font-size:9px;margin-top:12px}
.leg{padding:8px;margin-bottom:8px;background:#141922;border-radius:6px;border:1px solid #232d3d}
.leg h3{font-size:10px;color:#4a9eff;margin-bottom:4px;font-weight:bold}
.leg .row{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:9px;color:#94a3b8}
.leg .item{white-space:nowrap}
.leg .item b{color:#e2e8f0;font-weight:600}
.sec{background:#141922;border-radius:8px;margin-bottom:8px;border:1px solid #232d3d;overflow:hidden}
.sh{padding:12px;cursor:pointer;font-weight:bold;font-size:13px;display:flex;align-items:center;gap:8px;border-bottom:1px solid #232d3d}
.sh:active{background:#1a2030}
.sh .arr{transition:transform .2s;font-size:10px}
.sh.open .arr{transform:rotate(90deg)}
.sc{padding:12px;display:none}.sc.open{display:block}
h4{font-size:12px;color:#60a5fa;margin:12px 0 4px;font-weight:bold}
p{font-size:12px;color:#94a3b8;margin-bottom:8px}
ul{padding-left:16px;margin-bottom:8px}
li{font-size:12px;color:#94a3b8;margin-bottom:3px}
table{width:100%;border-collapse:collapse;margin:6px 0;font-size:11px}
th{background:#1e2635;padding:5px 6px;text-align:left;color:#fbbf24;font-weight:bold}
td{padding:5px 6px;border-bottom:1px solid #232d3d;color:#cbd5e1}
.note{background:rgba(245,158,11,.08);border-left:3px solid #f59e0b;padding:6px;border-radius:0 4px 4px 0;margin:6px 0;font-size:11px;color:#fbbf24}
.good{background:rgba(34,197,94,.08);border-left:3px solid #22c55e;padding:6px;border-radius:0 4px 4px 0;margin:6px 0;font-size:11px;color:#4ade80}
.bad{background:rgba(239,68,68,.08);border-left:3px solid #ef4444;padding:6px;border-radius:0 4px 4px 0;margin:6px 0;font-size:11px;color:#f87171}
.formula{background:#0e1117;padding:6px 8px;border-radius:4px;font-family:monospace;color:#4ade80;margin:4px 0;font-size:10px}
</style>
</head>
<body>
<button class="lng-btn" onclick="toggleLang()">EN</button>
<div class="hd">
<h1>PMR Daily Brief</h1>
<div class="s" id="sub">Brisbane + Gold Coast | 20 Properties | 3 Tiers</div>
<div id="date" class="s" style="color:#4a9eff"></div>
</div>
<div class="tabs">
<div class="tab act" onclick="show('t1')" id="tab1">Tier 1</div>
<div class="tab" onclick="show('t2')" id="tab2">Tier 2</div>
<div class="tab" onclick="show('t3')" id="tab3">Tier 3</div>
<div class="tab" onclick="show('ta')" id="taba">All</div>
<div class="tab" onclick="show('t4')" id="tab4">Guide</div>
</div>

<div class="nb">

<!-- TIER 1 -->
<div class="tp act" id="t1">

<div class="c"><div class="ch"><span class="rk r1">1</span><span class="nm">The Gap</span><a class="lk" href="https://accomproperties.com.au/business-display/business-the-gap,19190">&#x1f517;</a><span class="badge g">BEST</span></div>
<div class="pr">$790K</div>
<div class="mg">
<div class="mi"><div class="v g">$128K</div><div class="l">NetInc</div></div>
<div class="mi"><div class="v g">61.5%</div><div class="l">BC%</div></div>
<div class="mi"><div class="v g">$68/wk</div><div class="l">$/wk</div></div>
<div class="mi"><div class="v g">6.17x</div><div class="l">Mult</div></div>
<div class="mi"><div class="v g">14</div><div class="l">Pool</div></div>
<div class="mi"><div class="v g">23yr</div><div class="l">Cont</div></div>
</div>
<div class="rw g">
<span class="g-e">✅ BC 61.5% ideal | 23yr contract | $68/wk normal | Minimal no Gate</span>
<span class="g-z" style="display:none">✅ BC 61.5%理想 | 23年合同 | $68/周正常 | 极简无Gate</span>
</div>
<div class="rw">
<span class="g-e">⚠️ Total units unknown | 12 ext unit needs written BC confirmation</span>
<span class="g-z" style="display:none">⚠️ 总套数未知 | 12外部单元收回需书面确认</span>
</div>
<div class="ab"><b>
<span class="g-e">Action:</span><span class="g-z" style="display:none">行动:</span>
</b> <span class="g-e">Get total unit count + confirm 12 external units recovery</span><span class="g-z" style="display:none">获取总套数 + 确认12外部单元收回</span></div></div>

<div class="c"><div class="ch"><span class="rk r2">2</span><span class="nm">West End</span><a class="lk" href="https://accomproperties.com.au/business-display/business-west-end,19008">&#x1f517;</a><span class="badge g">HEALTHY</span></div>
<div class="pr">$750K</div>
<div class="mg"><div class="mi"><div class="v g">$125K</div><div class="l">NetInc</div></div><div class="mi"><div class="v g">61.1%</div><div class="l">BC%</div></div><div class="mi"><div class="v n">N/A</div><div class="l">$/wk</div></div><div class="mi"><div class="v g">5.99x</div><div class="l">Mult</div></div><div class="mi"><div class="v n">?</div><div class="l">Pool</div></div><div class="mi"><div class="v n">?</div><div class="l">Cont</div></div></div>
<div class="rw g"><span class="g-e">✅ BC 61.1% health | CPI annual | New building low maint</span><span class="g-z" style="display:none">✅ BC61.1%健康 | CPI递增 | 楼龄新</span></div>
<div class="rw"><span class="g-e">⚠️ Pool completely undisclosed = main risk</span><span class="g-z" style="display:none">⚠️ Pool数据全无 — 主要风险</span></div>
<div class="ab"><b><span class="g-e">Action:</span><span class="g-z" style="display:none">行动:</span></b> <span class="g-e">Get Pool + contract + total units</span><span class="g-z" style="display:none">获取Pool+合同+总套数</span></div></div>

<div class="c"><div class="ch"><span class="rk r3">3</span><span class="nm">Burleigh Waters</span><a class="lk" href="https://accomproperties.com.au/business-display/business-burleigh-waters,19099">&#x1f517;</a><span class="badge b">GC</span></div>
<div class="pr">$850K</div>
<div class="mg"><div class="mi"><div class="v g">$210K</div><div class="l">NetInc</div></div><div class="mi"><div class="v g">66.6%</div><div class="l">BC%</div></div><div class="mi"><div class="v g">$70K</div><div class="l">Letting</div></div><div class="mi"><div class="v g">4.05x</div><div class="l">Mult</div></div><div class="mi"><div class="v n">?</div><div class="l">Pool</div></div><div class="mi"><div class="v n">?</div><div class="l">Cont</div></div></div>
<div class="rw g"><span class="g-e">✅ BC 66.6% ideal | 4.05x excellent | Residency $610/wk extra</span><span class="g-z" style="display:none">✅ BC66.6%理想 | 4.05x极佳 | 住宅$610/周额外</span></div>
<div class="rw"><span class="g-e">⚠️ Pool + contract unverified</span><span class="g-z" style="display:none">⚠️ Pool/合同待核实</span></div>
<div class="ab"><b><span class="g-e">Action:</span><span class="g-z" style="display:none">行动:</span></b> <span class="g-e">Verify Pool + contract + units. Could be #1 if healthy</span><span class="g-z" style="display:none">核实Pool+合同。若健康可升#1</span></div></div>

<div class="c"><div class="ch"><span class="nm">4. Chermside</span><a class="lk" href="https://theonsitemanager.com.au/">&#x1f517;</a><span class="badge y">UNVERIFIED</span></div>
<div class="pr">$652K (2 complexes)</div>
<div class="bx"><span class="g-e">If $178K net confirmed → 3.66x excellent. But net income is unverified rumor. BC $90K+. If real, ROI 27.3%.</span><span class="g-z" style="display:none">若$178K净利属实→3.66x极佳。但净利未确认。BC $90K+。若属实，ROI 27.3%。</span></div>
<div class="ab"><b><span class="g-e">Action:</span><span class="g-z" style="display:none">行动:</span></b> <span class="g-e">Verify net income with Accom Properties. Priority #1</span><span class="g-z" style="display:none">联系Accom确认净利。第一优先</span></div></div>

<div class="c"><div class="ch"><span class="nm">5. Main Beach 2x $375K</span><a class="lk" href="https://accomproperties.com.au/business-display/business-main-beach,19111">&#x1f517;</a><span class="badge r">CARETAKER</span></div>
<div class="pr">$375K</div>
<div class="bx"><span class="g-e">BC83.7% + $24/wk very low. 2 adjoining complexes. Pool 8/42=19% growth potential. 16yr contract.</span><span class="g-z" style="display:none">BC83.7% + $24/周极低。相邻两栋。Pool 8/42=19%有增长潜力。16年合同。</span></div></div>

<div class="c"><div class="ch"><span class="nm">6. Wakerley $729K+$950K=$1.67M</span></div>
<div class="bx"><span class="g-e">Price cut for quick sale + topped up. But all data missing — net, BC, contract, pool unknown.</span><span class="g-z" style="display:none">降价急售+已top-up。但所有数据缺失。</span></div></div>

<div class="c"><div class="ch"><span class="nm">7. Kangaroo Pt $105K</span><span class="badge r">CARETAKER</span></div>
<div class="bx"><span class="g-e">BC100% pure caretaker. No letting. 21 units, 20 owner-occupied. Only portfolio add-on.</span><span class="g-z" style="display:none">BC100%纯caretaker，无letting。仅portfolio附加。</span></div></div>

<div class="c"><div class="ch"><span class="nm">8. Brisbane City $608K</span><a class="lk" href="https://accomproperties.com.au/business-display/business-brisbane-city,19124">&#x1f517;</a><span class="badge r">NO DATA</span></div>
<div class="bx"><span class="g-e">All operating data completely undisclosed. Lowest entry but risk unknown.</span><span class="g-z" style="display:none">所有运营数据未披露。最低门槛但风险未知。</span></div>
<div class="ab"><b><span class="g-e">Action:</span><span class="g-z" style="display:none">行动:</span></b> <span class="g-e">Get full info pack. If refused, ignore</span><span class="g-z" style="display:none">获取完整信息包。若拒绝则忽略</span></div></div>

<div class="c"><div class="ch"><span class="nm">9. Silver Quays $691K</span><a class="lk" href="https://accomproperties.com.au/business-display/business-kangaroo-point,19211">&#x1f517;</a><span class="badge r">TRAP</span></div>
<div class="bx"><span class="g-e">BC93.6%=caretaker + $34/wk extremely low. Pool 5/49=10.2%. IGNORE.</span><span class="g-z" style="display:none">BC93.6%=caretaker + $34/周极低。Pool仅5/49。忽略。</span></div></div>

<div class="c"><div class="ch"><span class="nm">10. Mermaid Waters $1.6M</span><span class="badge y">OVER BUDGET</span></div>
<div class="bx"><span class="g-e">GC. Net $80K, Remun $71K. BC 89.5% borderline caretaker. Over Tier1.</span><span class="g-z" style="display:none">GC。Net $80K, Pool 5。BC 89.5%接近caretaker。超Tier1。</span></div></div>

<div class="c"><div class="ch"><span class="nm">11. Broadbeach Waters</span><a class="lk" href="https://accomproperties.com.au/management-rights-for-sale-gold-coast">&#x1f517;</a><span class="badge b">NEW</span></div>
<div class="bx"><span class="g-e">$115K net. No RE buy, no onsite, no office hours. Price/BC/Pool unknown.</span><span class="g-z" style="display:none">净$115K。无需购房+无onsite+无办公。价格/BC/Pool均未知。</span></div>
<div class="ab"><b><span class="g-e">Action:</span><span class="g-z" style="display:none">行动:</span></b> <span class="g-e">Get price/BC/Pool data</span><span class="g-z" style="display:none">获取价格/BC/Pool数据</span></div></div>

<div class="c"><div class="ch"><span class="nm">12. Mermaid Beach $220K</span><span class="badge r">SKIP</span></div>
<div class="bx"><span class="g-e">GC Mermaid Beach. $220K caretaking only. Ignore.</span><span class="g-z" style="display:none">GC Mermaid Beach。$220K caretaking。忽略。</span></div></div>

<div class="c"><div class="ch"><span class="nm">13. Brisbane Tender 4/17</span><a class="lk" href="https://accomproperties.com.au/business-display/business-brisbane-city,19103">&#x1f517;</a><span class="badge b">4/17</span></div>
<div class="bx"><span class="g-e">Service + letting agent authority. No unit cost. Closes Apr 17 4PM. All data undisclosed.</span><span class="g-z" style="display:none">服务协议+租赁代理。不需购unit。截止4/17 4PM。全数据未披露。</span></div></div>

</div>

<!-- TIER 2 -->
<div class="tp" id="t2">

<div class="c"><div class="ch"><span class="rk r3">T1</span><span class="nm">Teneriffe</span><a class="lk" href="https://accomproperties.com.au/business-display/business-teneriffe,19064">&#x1f517;</a><span class="badge y">MISSING</span></div>
<div class="pr">$1,357K</div>
<div class="mg"><div class="mi"><div class="v n">N/A</div><div class="l">NetInc</div></div><div class="mi"><div class="v n">N/A</div><div class="l">BC%</div></div><div class="mi"><div class="v n">N/A</div><div class="l">Pool</div></div><div class="mi"><div class="v n">N/A</div><div class="l">Cont</div></div><div class="mi"><div class="v n">N/A</div><div class="l">Mult</div></div><div class="mi"><div class="v n">N/A</div><div class="l">$/wk</div></div></div>
<div class="rw"><span class="g-e">⚠️ Blue-chip Teneriffe near CBD+Riverwalk | All data missing | $1.36M over budget</span><span class="g-z" style="display:none">⚠️ Teneriffe蓝钻地段 | 全数据缺失 | 超预算</span></div>
<div class="ab"><b><span class="g-e">Action:</span><span class="g-z" style="display:none">行动:</span></b> <span class="g-e">Get full disclosure from Resort Brokers</span><span class="g-z" style="display:none">从Resort Brokers获取完整披露</span></div></div>

<div class="c"><div class="ch"><span class="nm">T2. Bulimba</span><a class="lk" href="https://accomproperties.com.au/business-display/business-bulimba,18986">&#x1f517;</a></div>
<div class="pr">$1,350K MR + $790K Unit = $2.14M Total</div>
<div class="mg"><div class="mi"><div class="v g">$257K</div><div class="l">NetInc</div></div><div class="mi"><div class="v g">5.25x</div><div class="l">Mult</div></div><div class="mi"><div class="v n">N/A</div><div class="l">BC%</div></div><div class="mi"><div class="v n">N/A</div><div class="l">Pool</div></div><div class="mi"><div class="v n">N/A</div><div class="l">Cont</div></div><div class="mi"><div class="v n">N/A</div><div class="l">$/wk</div></div></div>
<div class="bx"><span class="g-e">Net $257K healthy, 5.25x OK, blue-chip Bulimba. But total $2.14M.</span><span class="g-z" style="display:none">净利$257K健康，5.25x可以，Bulimba蓝钻地段。但总投入$2.14M。</span></div>
<div class="ab"><b><span class="g-e">Action:</span><span class="g-z" style="display:none">行动:</span></b> <span class="g-e">Get full disclosure</span><span class="g-z" style="display:none">获取完整披露</span></div></div>

<div class="c"><div class="ch"><span class="nm">T3. Clontarf $1,100K</span><span class="badge y">NEEDS DD</span></div>
<div class="bx"><span class="g-e">Clontarf MR. Needs DD on BC/Pool/Contract/Net.</span><span class="g-z" style="display:none">Clontarf MR。需尽调BC/Pool/合同。</span></div></div>

</div>

<!-- TIER 3 -->
<div class="tp" id="t3">

<div class="c"><div class="ch"><span class="nm">T4. Brisbane CBD Waterfront</span><a class="lk" href="https://accomproperties.com.au/business-display/business-brisbane-city,19147">&#x1f517;</a></div>
<div class="pr">$2,905K</div>
<div class="mg"><div class="mi"><div class="v g">$431K</div><div class="l">NetInc</div></div><div class="mi"><div class="v g">57.5%</div><div class="l">BC%</div></div><div class="mi"><div class="v g">52</div><div class="l">Pool</div></div><div class="mi"><div class="v y">150</div><div class="l">Total</div></div><div class="mi"><div class="v y">8yr</div><div class="l">Cont</div></div><div class="mi"><div class="v y">6.7x</div><div class="l">Mult</div></div></div>
<div class="rw g"><span class="g-e">✅ BC 57.5% health | $431K net | 52Pool | top-up history</span><span class="g-z" style="display:none">✅ BC57.5%健康 | $431K净利 | 52Pool | top-up历史</span></div>
<div class="rw"><span class="g-e">⚠️ $2.9M over budget | 8yr contract short | 150-unit complex</span><span class="g-z" style="display:none">⚠️ $2.9M超预算 | 合同仅8年 | 150单元complex</span></div>
<div class="ab"><b><span class="g-e">Verdict:</span><span class="g-z" style="display:none">结论:</span></b> <span class="g-e">Excellent fundamentals but too big now</span><span class="g-z" style="display:none">基本面极佳但现在太大</span></div></div>

<div class="c"><div class="ch"><span class="nm">T5. Mermaid Beach Premium</span><a class="lk" href="https://accomproperties.com.au/business-display/business-mermaid-beach,18815">&#x1f517;</a></div>
<div class="pr">$1,890K</div>
<div class="mg"><div class="mi"><div class="v g">$240K</div><div class="l">NetInc</div></div><div class="mi"><div class="v g">52%</div><div class="l">BC%</div></div><div class="mi"><div class="v g">18</div><div class="l">Pool</div></div><div class="mi"><div class="v g">47</div><div class="l">Total</div></div><div class="mi"><div class="v g">21yr</div><div class="l">Cont</div></div><div class="mi"><div class="v y">7.9x</div><div class="l">Mult</div></div></div>
<div class="rw g"><span class="g-e">✅ BC 52% very healthy | 21yr | 48% from letting | Holiday+Permanent mix</span><span class="g-z" style="display:none">✅ BC52%极健 | 21年 | 48%租赁 | 混合模式</span></div>
<div class="rw g"><span class="g-e">✅ No onsite | No office hrs | Manager unit $850K extra</span><span class="g-z" style="display:none">✅ 无需住onsite | 无办公 | 经理unit $850K额外</span></div>
<div class="rw"><span class="g-e">⚠️ $1.89M over | 7.87x high</span><span class="g-z" style="display:none">⚠️ $1.89M超预算 | 7.87x倍数偏高</span></div>
<div class="ab"><b><span class="g-e">Verdict:</span><span class="g-z" style="display:none">结论:</span></b> <span class="g-e">BEST in Tier2+. When budget expands, pick this first</span><span class="g-z" style="display:none">Tier2+最佳。预算扩展时首选</span></div></div>

<div class="c"><div class="ch"><span class="nm">T6. Palm Beach Mixed $1.55M</span><a class="lk" href="https://accomproperties.com.au/business-display/business-palm-beach,19062">&#x1f517;</a></div>
<div class="pr">$1,550K</div>
<div class="mg"><div class="mi"><div class="v y">16/28</div><div class="l">Pool</div></div><div class="mi"><div class="v g">57%</div><div class="l">Ratio</div></div><div class="mi"><div class="v g">18yr</div><div class="l">Cont</div></div><div class="mi"><div class="v n">N/A</div><div class="l">NetInc</div></div><div class="mi"><div class="v n">N/A</div><div class="l">BC</div></div><div class="mi"><div class="v n">N/A</div><div class="l">$/wk</div></div></div>
<div class="rw g"><span class="g-e">✅ 16/28=57% Pool ratio excellent | 18yr contract</span><span class="g-z" style="display:none">✅ 16/28=57%Pool比例极佳 | 18年合同</span></div>
<div class="rw"><span class="g-e">⚠️ Net/BC unknown | $1.55M over</span><span class="g-z" style="display:none">⚠️ 净利/BC未知 | $1.55M超预算</span></div></div>

<div class="c"><div class="ch"><span class="nm">T7. Mansfield $1,600K</span></div>
<div class="pr">$1,600K</div>
<div class="bx"><span class="g-e">Needs DD on all operating data. No detailed info yet.</span><span class="g-z" style="display:none">需尽调所有运营数据。目前无详细信息。</span></div>
<div class="ab"><b><span class="g-e">Action:</span><span class="g-z" style="display:none">行动:</span></b> <span class="g-e">Request full info package</span><span class="g-z" style="display:none">获取完整信息包</span></div></div>

</div>

<!-- ALL TABLE -->
<div class="tp" id="ta">
<div class="tw"><table class="t"><thead><tr>
<th>#</th><th id="th-n">Name</th><th>T</th><th id="th-pr">Price</th><th id="th-ni">Net</th><th>BC%</th><th>Mult</th><th>P</th><th id="th-trap">Trap</th>
</tr></thead><tbody>
<tr><td>1</td><td>The Gap</td><td style="color:#22c55e">1</td><td style="color:#22c55e">$790K</td><td style="color:#22c55e">$128K</td><td style="color:#22c55e">62%</td><td style="color:#fbbf24">6.17x</td><td style="color:#22c55e">14</td><td style="color:#22c55e">N</td></tr>
<tr><td>2</td><td>West End</td><td style="color:#22c55e">1</td><td style="color:#22c55e">$750K</td><td style="color:#22c55e">$125K</td><td style="color:#22c55e">61%</td><td style="color:#22c55e">5.99x</td><td style="color:#4b5563">?</td><td style="color:#22c55e">N</td></tr>
<tr><td>3</td><td>Burleigh Wt</td><td style="color:#22c55e">1</td><td style="color:#22c55e">$850K</td><td style="color:#22c55e">$210K</td><td style="color:#22c55e">67%</td><td style="color:#22c55e">4.05x</td><td style="color:#4b5563">?</td><td style="color:#22c55e">N</td></tr>
<tr><td>4</td><td>Chermside</td><td style="color:#22c55e">1</td><td style="color:#22c55e">$652K</td><td style="color:#4b5563">?</td><td style="color:#4b5563">?</td><td style="color:#4b5563">3.7x?</td><td style="color:#4b5563">?</td><td style="color:#fbbf24">?</td></tr>
<tr><td>5</td><td>Main Bch 2x</td><td style="color:#22c55e">1</td><td style="color:#22c55e">$375K</td><td style="color:#22c55e">$94K</td><td style="color:#ef4444">84%</td><td style="color:#22c55e">4.0x</td><td style="color:#fbbf24">8</td><td style="color:#ef4444">Y</td></tr>
<tr><td>6</td><td>Wakerley</td><td style="color:#22c55e">1</td><td style="color:#fbbf24">$1.7M</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">?</td></tr>
<tr><td>7</td><td>Kangaroo Pt</td><td style="color:#22c55e">1</td><td style="color:#22c55e">$105K</td><td style="color:#22c55e">$25K</td><td style="color:#ef4444">100%</td><td style="color:#22c55e">4.1x</td><td style="color:#ef4444">0</td><td style="color:#ef4444">Y</td></tr>
<tr><td>8</td><td>Bris City</td><td style="color:#22c55e">1</td><td style="color:#22c55e">$608K</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">?</td></tr>
<tr><td>9</td><td>Silver Quays</td><td style="color:#22c55e">1</td><td style="color:#22c55e">$691K</td><td style="color:#22c55e">$138K</td><td style="color:#ef4444">94%</td><td style="color:#22c55e">5.0x</td><td style="color:#fbbf24">5</td><td style="color:#ef4444">Y</td></tr>
<tr><td>10</td><td>Mrd Wtrs</td><td style="color:#22c55e">1</td><td style="color:#fbbf24">$1.6M</td><td style="color:#22c55e">$80K</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#fbbf24">5</td><td style="color:#fbbf24">?</td></tr>
<tr><td>11</td><td>Broadbeach W</td><td style="color:#22c55e">1</td><td style="color:#4b5563">?</td><td style="color:#22c55e">$115K</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">?</td></tr>
<tr><td>12</td><td>Mrd Bch CT</td><td style="color:#22c55e">1</td><td style="color:#22c55e">$220K</td><td style="color:#4b5563">?</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#ef4444">Y</td></tr>
<tr style="border-bottom:2px solid #22c55e"><td>13</td><td>Tender 4/17</td><td style="color:#22c55e">1</td><td style="color:#4b5563">?</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">?</td></tr>
<tr style="border-top:2px solid #fbbf24"><td>T1</td><td>Teneriffe</td><td style="color:#fbbf24">2</td><td style="color:#fbbf24">$1.4M</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">?</td></tr>
<tr><td>T2</td><td>Bulimba</td><td style="color:#fbbf24">2</td><td style="color:#fbbf24">$1.4M</td><td style="color:#22c55e">$257K</td><td style="color:#4b5563">-</td><td style="color:#22c55e">5.25x</td><td style="color:#4b5563">-</td><td style="color:#4b5563">?</td></tr>
<tr style="border-bottom:2px solid #fbbf24"><td>T3</td><td>Clontarf</td><td style="color:#fbbf24">2</td><td style="color:#fbbf24">$1.1M</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">?</td></tr>
<tr style="border-top:2px solid #a855f7"><td>T4</td><td>Bris CBD Wtr</td><td style="color:#a855f7">3</td><td style="color:#a855f7">$2.9M</td><td style="color:#22c55e">$431K</td><td style="color:#22c55e">58%</td><td style="color:#fbbf24">6.7x</td><td style="color:#22c55e">52</td><td style="color:#22c55e">N</td></tr>
<tr><td>T5</td><td>Mermaid Bch</td><td style="color:#a855f7">3</td><td style="color:#a855f7">$1.9M</td><td style="color:#22c55e">$240K</td><td style="color:#22c55e">52%</td><td style="color:#fbbf24">7.9x</td><td style="color:#fbbf24">18</td><td style="color:#22c55e">N</td></tr>
<tr><td>T6</td><td>Palm Beach</td><td style="color:#a855f7">3</td><td style="color:#a855f7">$1.6M</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#fbbf24">16</td><td style="color:#4b5563">?</td></tr>
<tr style="border-bottom:2px solid #a855f7"><td>T7</td><td>Mansfield</td><td style="color:#a855f7">3</td><td style="color:#a855f7">$1.6M</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">-</td><td style="color:#4b5563">?</td></tr>
</tbody></table></div>
</div>

<!-- GUIDE TAB -->
<div class="tp" id="t4">

<div class="sec">
<div class="sh open" onclick="toggle(this)"><span class="arr">&#x25B6;</span>
<span class="g-e">1. What is PMR?</span><span class="g-z" style="display:none">1. 什么是PMR？</span></div>
<div class="sc open">
<p><span class="g-e">PMR (Property Management Rights) is a uniquely Australian business model, most common in Queensland. It combines two roles:</span>
<span class="g-z" style="display:none">PMR（物业管理权）是澳大利亚独特的商业模式，在昆士兰最常见。它结合两个角色：</span></p>
<ul>
<li><b><span class="g-e">Caretaking</span><span class="g-z" style="display:none">物业管理</span></b> <span class="g-e">— maintaining common areas (gardens, pools, BBQ areas)</span><span class="g-z" style="display:none">— 维护公共区域（花园、泳池、BBQ等）</span></li>
<li><b><span class="g-e">Letting</span><span class="g-z" style="display:none">租赁管理</span></b> <span class="g-e">— managing short-term or long-term rentals for unit owners</span><span class="g-z" style="display:none">— 为业主管理短租或长租</span></li>
</ul>
<div class="note">💡 <span class="g-e">You buy the <b>business agreement</b> (the right to manage), not the property itself.</span><span class="g-z" style="display:none">你购买的是<b>经营管理权协议</b>（经营权），不是房产本身。</span></div>
<h4><span class="g-e">Three Types</span><span class="g-z" style="display:none">三种类型</span></h4>
<table><tr><th><span class="g-e">Type</span><span class="g-z" style="display:none">类型</span></th><th><span class="g-e">What You Buy</span><span class="g-z" style="display:none">购买内容</span></th><th><span class="g-e">Typical Price</span><span class="g-z" style="display:none">典型价格</span></th></tr>
<tr><td><span class="g-e">Business Only</span><span class="g-z" style="display:none">纯商业</span></td><td><span class="g-e">Caretaking + Letting agreement</span><span class="g-z" style="display:none">管理+租赁协议</span></td><td>$500K - $1.5M</td></tr>
<tr><td><span class="g-e">MR + Unit</span><span class="g-z" style="display:none">MR+公寓</span></td><td><span class="g-e">PMR business + manager's apartment</span><span class="g-z" style="display:none">PMR业务+经理公寓</span></td><td>$1M - $3M+</td></tr>
<tr><td><span class="g-e">MR + Freehold</span><span class="g-z" style="display:none">MR+产权</span></td><td><span class="g-e">PMR business + own a unit</span><span class="g-z" style="display:none">PMR业务+拥有unit</span></td><td>$2M - $5M+</td></tr></table>
<h4><span class="g-e">Permanent vs Holiday</span><span class="g-z" style="display:none">长租 vs 短租</span></h4>
<ul>
<li><b><span class="g-e">Permanent</span><span class="g-z" style="display:none">长租</span></b> <span class="g-e">— long-term rentals (6-12 months), stable income</span><span class="g-z" style="display:none">— 长期租赁（6-12个月），收入稳定</span></li>
<li><b><span class="g-e">Holiday</span><span class="g-z" style="display:none">短租</span></b> <span class="g-e">— short-term bookings (Airbnb-style), higher returns, more work</span><span class="g-z" style="display:none">— 短期预订（Airbnb式），回报更高，工作更多</span></li>
<li><b><span class="g-e">Mixed</span><span class="g-z" style="display:none">混合</span></b> <span class="g-e">— both (most versatile but most complex)</span><span class="g-z" style="display:none">— 两者结合（功能多但复杂）</span></li>
</ul>
</div></div>

<div class="sec">
<div class="sh" onclick="toggle(this)"><span class="arr">&#x25B6;</span>
<span class="g-e">2. How to Evaluate a Deal</span><span class="g-z" style="display:none">2. 如何评估PMR交易</span></div>
<div class="sc">
<h4><span class="g-e">① BC Salary % — THE Most Important Metric</span><span class="g-z" style="display:none">① BC薪资占比 — 最重要的指标</span></h4>
<div class="formula">BC% = BC Salary / Net Income × 100</div>
<table><tr><th>BC%</th><th><span class="g-e">Meaning</span><span class="g-z" style="display:none">含义</span></th><th><span class="g-e">Action</span><span class="g-z" style="display:none">行动</span></th></tr>
<tr><td style="color:#22c55e"><b>50-70%</b></td><td style="color:#22c55e"><span class="g-e">Healthy balance</span><span class="g-z" style="display:none">理想</span></td><td style="color:#22c55e">✅ <span class="g-e">Good PMR</span><span class="g-z" style="display:none">良好</span></td></tr>
<tr><td style="color:#fbbf24"><b>70-80%</b></td><td style="color:#fbbf24"><span class="g-e">Leaning caretaker</span><span class="g-z" style="display:none">注意</span></td><td style="color:#fbbf24">⚠️ <span class="g-e">Caution</span><span class="g-z" style="display:none">谨慎</span></td></tr>
<tr><td style="color:#ef4444"><b>&gt;80%</b></td><td style="color:#ef4444"><span class="g-e">🚨 Caretaker trap!</span><span class="g-z" style="display:none">🚨 纯caretaker陷阱</span></td><td style="color:#ef4444">❌ <span class="g-e">Avoid!</span><span class="g-z" style="display:none">避免！</span></td></tr></table>

<h4><span class="g-e">② Multiplier (Price / Net Income)</span><span class="g-z" style="display:none">② 倍数（价格/净收入）</span></h4>
<div class="formula">Multiplier = Price / Net Profit</div>
<table><tr><th><span class="g-e">Multiplier</span><span class="g-z" style="display:none">倍数</span></th><th><span class="g-e">Assessment</span><span class="g-z" style="display:none">评估</span></th></tr>
<tr><td style="color:#22c55e"><b>3-5x</b></td><td style="color:#22c55e"><span class="g-e">Excellent (recoup in 3-5 yrs)</span><span class="g-z" style="display:none">极佳（3-5年回本）</span></td></tr>
<tr><td style="color:#fbbf24"><b>5-6x</b></td><td style="color:#fbbf24"><span class="g-e">Fair market value</span><span class="g-z" style="display:none">合理市场价</span></td></tr>
<tr><td style="color:#ef4444"><b>&gt;6x</b></td><td style="color:#ef4444"><span class="g-e">Overpriced</span><span class="g-z" style="display:none">过高</span></td></tr></table>

<h4><span class="g-e">③ Commission Per Unit Per Week</span><span class="g-z" style="display:none">③ 每单元周佣金（$/wk）</span></h4>
<div class="formula">$/wk = (Net Income − BC Salary) / Pool Units / 52</div>
<table><tr><th>$/wk</th><th><span class="g-e">Meaning</span><span class="g-z" style="display:none">含义</span></th></tr>
<tr><td style="color:#22c55e"><b>$60-85</b></td><td style="color:#22c55e"><span class="g-e">Normal Brisbane range</span><span class="g-z" style="display:none">正常范围</span></td></tr>
<tr><td style="color:#fbbf24"><b>$40-60</b></td><td style="color:#fbbf24"><span class="g-e">Below average</span><span class="g-z" style="display:none">低于平均</span></td></tr>
<tr><td style="color:#ef4444"><b>&lt;$40</b></td><td style="color:#ef4444"><span class="g-e">🚨 Abnormally low — investigate!</span><span class="g-z" style="display:none">🚨 极低 — 需要调查！</span></td></tr></table>

<h4><span class="g-e">④ Contract Years Remaining</span><span class="g-z" style="display:none">④ 合同剩余年限</span></h4>
<table><tr><th><span class="g-e">Years</span><span class="g-z" style="display:none">年限</span></th><th><span class="g-e">Meaning</span><span class="g-z" style="display:none">含义</span></th></tr>
<tr><td style="color:#22c55e"><b>15+</b></td><td style="color:#22c55e"><span class="g-e">Excellent security</span><span class="g-z" style="display:none">极佳安全性</span></td></tr>
<tr><td style="color:#fbbf24"><b>10-15</b></td><td style="color:#fbbf24"><span class="g-e">Good — verify top-up history</span><span class="g-z" style="display:none">良好 — 查top-up历史</span></td></tr>
<tr><td style="color:#ef4444"><b>&lt;10</b></td><td style="color:#ef4444"><span class="g-e">🚨 Risk — needs top-up strategy</span><span class="g-z" style="display:none">🚨 风险 — 需要top-up策略</span></td></tr></table>

<h4><span class="g-e">⑤ Operational Burden</span><span class="g-z" style="display:none">⑤ 运营负担</span></h4>
<ul>
<li><span class="g-e">On-site required? (Must you live there?)</span><span class="g-z" style="display:none">必须住onsite？</span></li>
<li><span class="g-e">Fixed office hours? (vs flexible "contactable")</span><span class="g-z" style="display:none">固定办公时间？vs 灵活联系</span></li>
<li><span class="g-e">Facilities: Pool? Gym? BBQ? Lift? (More = more work)</span><span class="g-z" style="display:none">设施：泳池？健身房？（越多=工作量越大）</span></li>
<li><span class="g-e">Can you outsource cleaning/gardening? (Ideal)</span><span class="g-z" style="display:none">能否外包清洁/园艺？（理想）</span></li>
</ul>
</div></div>

<div class="sec">
<div class="sh" onclick="toggle(this)"><span class="arr">&#x25B6;</span>
<span class="g-e">3. Financial Analysis</span><span class="g-z" style="display:none">3. 财务分析</span></div>
<div class="sc">
<h4><span class="g-e">Return on Investment (ROI)</span><span class="g-z" style="display:none">投资回报率（ROI）</span></h4>
<div class="formula">ROI = (Net Income / Asking Price) × 100</div>
<table><tr><th>ROI</th><th><span class="g-e">Assessment</span><span class="g-z" style="display:none">评估</span></th></tr>
<tr><td style="color:#22c55e"><b>15-25%</b></td><td style="color:#22c55e"><span class="g-e">Strong return</span><span class="g-z" style="display:none">强回报</span></td></tr>
<tr><td style="color:#fbbf24"><b>10-15%</b></td><td style="color:#fbbf24"><span class="g-e">Market average</span><span class="g-z" style="display:none">市场平均</span></td></tr>
<tr><td style="color:#ef4444"><b>&lt;10%</b></td><td style="color:#ef4444"><span class="g-e">Weak — reconsider</span><span class="g-z" style="display:none">弱 — 重新考虑</span></td></tr></table>

<h4><span class="g-e">Leveraged Return (With Mortgage)</span><span class="g-z" style="display:none">杠杆回报（含按揭）</span></h4>
<div class="formula">Cash Flow = Net Income − Annual Mortgage Payment</div>
<p><span class="g-e">Example: $800K deal, 70% LVR @ 6% interest = ~$33K/yr mortgage</span>
<span class="g-z" style="display:none">示例：$800K交易，70%贷款@6%利率 = ~$33K/年按揭</span></p>
<div class="formula">$128K − $33K = $95K <span class="g-e">free cash flow</span><span class="g-z" style="display:none">净现金流</span></div>
<div class="note">💡 <span class="g-e">BC salary increases by CPI only. Letting income GROWS with occupancy, rates, and pool expansion!</span>
<span class="g-z" style="display:none">BC薪资只随CPI增加。Letting收入随入住率和费率增长！</span></div>

<h4><span class="g-e">Typical Operating Costs</span><span class="g-z" style="display:none">典型运营成本</span></h4>
<ul>
<li><span class="g-e">Cleaning/maintenance: $5K-$15K/yr</span><span class="g-z" style="display:none">清洁/维护：$5K-$15K/年</span></li>
<li><span class="g-e">Marketing/ads: $3K-$8K/yr</span><span class="g-z" style="display:none">营销：$3K-$8K/年</span></li>
<li><span class="g-e">Insurance: $2K-$5K/yr</span><span class="g-z" style="display:none">保险：$2K-$5K/年</span></li>
<li><span class="g-e">Software/accounting: $2K-$4K/yr</span><span class="g-z" style="display:none">软件/会计：$2K-$4K/年</span></li>
<li><span class="g-e">Staff (if employed): $40K-$80K/yr</span><span class="g-z" style="display:none">员工（雇用）：$40K-$80K/年</span></li>
</ul>
</div></div>

<div class="sec">
<div class="sh" onclick="toggle(this)"><span class="arr">&#x25B6;</span>
<span class="g-e">4. Market Overview</span><span class="g-z" style="display:none">4. 市场概况</span></div>
<div class="sc">
<h4>Brisbane</h4>
<ul>
<li><span class="g-e">~600+ complexes</span><span class="g-z" style="display:none">~600+ 个complexes</span></li>
<li><span class="g-e">Strong demand: 2032 Olympics</span><span class="g-z" style="display:none">需求强劲：2032奥运会</span></li>
<li><span class="g-e">Typical multiplier: 5-7x (permanent)</span><span class="g-z" style="display:none">典型倍数：5-7x（长租）</span></li>
<li><span class="g-e">Average net yield: 15-20%</span><span class="g-z" style="display:none">平均净收益：15-20%</span></li>
</ul>
<h4>Gold Coast</h4>
<ul>
<li><span class="g-e">~1,200+ complexes (largest in Australia)</span><span class="g-z" style="display:none">~1,200+ 个（澳洲最大）</span></li>
<li><span class="g-e">Holiday/short-term dominant</span><span class="g-z" style="display:none">度假/短租主导</span></li>
<li><span class="g-e">Higher volatility but higher returns</span><span class="g-z" style="display:none">波动大但回报更高</span></li>
<li><span class="g-e">Average net yield: 18-25%</span><span class="g-z" style="display:none">平均净收益：18-25%</span></li>
</ul>
<h4><span class="g-e">2026 Trends</span><span class="g-z" style="display:none">2026趋势</span></h4>
<ul>
<li><span class="g-e">Rates stabilizing ~5.8-6.2%</span><span class="g-z" style="display:none">利率稳定在~5.8-6.2%</span></li>
<li><span class="g-e">Olympics infrastructure driving growth</span><span class="g-z" style="display:none">奥运会基础设施驱动增长</span></li>
<li><span class="g-e">Tourism recovery boosting short-term lets</span><span class="g-z" style="display:none">旅游业复苏推动短租</span></li>
<li><span class="g-e">PMR prices up ~8% year-on-year</span><span class="g-z" style="display:none">PMR价格同比涨~8%</span></li>
</ul>
</div></div>

<div class="sec">
<div class="sh" onclick="toggle(this)"><span class="arr">&#x25B6;</span>
<span class="g-e">5. Red Flags</span><span class="g-z" style="display:none">5. 红旗警告</span></div>
<div class="sc">
<div class="bad">🚨 <span class="g-e">BC Salary &gt;80% = Caretaker trap, no real letting business</span>
<span class="g-z" style="display:none">BC薪资&gt;80% = 纯caretaker陷阱，没有真正的letting业务</span></div>
<div class="bad">🚨 <span class="g-e">Contract &lt;8 years — Top-up may fail</span>
<span class="g-z" style="display:none">合同&lt;8年 — Top-up可能失败</span></div>
<div class="bad">🚨 <span class="g-e">Hostile BC — Check meeting minutes</span>
<span class="g-z" style="display:none">敌对BC — 检查会议纪要</span></div>
<div class="bad">🚨 <span class="g-e">Maintenance backlog — Your workload doubles</span>
<span class="g-z" style="display:none">维护积压 — 工作量翻倍</span></div>
<div class="bad">🚨 <span class="g-e">Owner-occupiers &gt;60% — Oppose short-term lets</span>
<span class="g-z" style="display:none">自住业主&gt;60% — 反对短租</span></div>
<div class="good">✅ <span class="g-e">History of successful top-ups = supportive BC</span>
<span class="g-z" style="display:none">成功top-up历史 = 支持性BC</span></div>
<div class="good">✅ <span class="g-e">High occupancy rate = strong demand</span>
<span class="g-z" style="display:none">高入住率 = 强劲需求</span></div>
<div class="good">✅ <span class="g-e">Can outsource cleaning/gardening = lower workload</span>
<span class="g-z" style="display:none">能外包清洁 = 低工作量</span></div>
</div></div>

<div class="sec">
<div class="sh" onclick="toggle(this)"><span class="arr">&#x25B6;</span>
<span class="g-e">6. Resources</span><span class="g-z" style="display:none">6. 资源</span></div>
<div class="sc">
<h4><span class="g-e">Industry Bodies</span><span class="g-z" style="display:none">行业协会</span></h4>
<ul>
<li><b>ARAMA QLD</b> — <span class="g-e">Industry body for PMR operators</span><span class="g-z" style="display:none">PMR运营商行业组织</span></li>
<li><b>AMRTA</b> — <span class="g-e">Accredited Management Rights Training Academy</span><span class="g-z" style="display:none">物业管理权培训认证学院</span></li>
</ul>
<h4><span class="g-e">Key Brokers</span><span class="g-z" style="display:none">关键经纪人</span></h4>
<ul>
<li><b>Accom Properties</b> — <span class="g-e">Largest QLD PMR broker</span><span class="g-z" style="display:none">最大QLD PMR经纪人</span></li>
<li><b>Resort Brokers</b> — <span class="g-e">Major hospitality/PMR broker</span><span class="g-z" style="display:none">主要酒店/PMR经纪人</span></li>
<li><b>TheOnsiteManager.com.au</b> — <span class="g-e">Industry portal</span><span class="g-z" style="display:none">行业门户</span></li>
<li><b>HotelResortSales.com.au</b> — <span class="g-e">Gold Coast specialist</span><span class="g-z" style="display:none">Gold Coast专家</span></li>
</ul>
<h4><span class="g-e">Further Reading</span><span class="g-z" style="display:none">延伸阅读</span></h4>
<ul>
<li>"Management Rights Buyers Guide" — <span class="g-e">Free PDF from AMRTA</span><span class="g-z" style="display:none">AMRTA免费PDF</span></li>
<li><span class="g-e">BCCM Act 1997</span> — <span class="g-e">The governing legislation</span><span class="g-z" style="display:none">管辖法律</span></li>
</ul>
</div></div>

</div>

</div>

<div class="ft">pmr-data-latest.json | 20 props | <span class="g-e">Auto-updated via GitHub Pages</span><span class="g-z" style="display:none">通过GitHub Pages自动更新</span></div>

<script>
var lang='en';
function toggleLang(){
  lang=(lang==='en')?'zh':'en';
  document.querySelector('.lng-btn').textContent=(lang==='zh')?'中文':'EN';
  document.querySelectorAll('.g-e').forEach(function(e){e.style.display=(lang==='zh')?'none':''});
  document.querySelectorAll('.g-z').forEach(function(e){e.style.display=(lang==='zh')?'':'none'});
  if(lang==='zh'){
    document.getElementById('sub').textContent='布里斯班 + 黄金海岸 | 20 物业 | 3个档位';
    document.getElementById('tab1').textContent='第1档';document.getElementById('tab2').textContent='第2档';
    document.getElementById('tab3').textContent='第3档';document.getElementById('taba').textContent='全部';
    document.getElementById('tab4').textContent='指南';
    document.getElementById('th-n').textContent='名称';document.getElementById('th-pr').textContent='价格';
    document.getElementById('th-ni').textContent='净利';document.getElementById('th-trap').textContent='陷阱';
  } else {
    document.getElementById('sub').textContent='Brisbane + Gold Coast | 20 Properties | 3 Tiers';
    document.getElementById('tab1').textContent='Tier 1';document.getElementById('tab2').textContent='Tier 2';
    document.getElementById('tab3').textContent='Tier 3';document.getElementById('taba').textContent='All';
    document.getElementById('tab4').textContent='Guide';
    document.getElementById('th-n').textContent='Name';document.getElementById('th-pr').textContent='Price';
    document.getElementById('th-ni').textContent='Net';document.getElementById('th-trap').textContent='Trap';
  }
}
function show(id){
  document.querySelectorAll('.tp').forEach(function(e){e.classList.remove('act')});
  document.querySelectorAll('.tab').forEach(function(e){e.classList.remove('act')});
  document.getElementById(id).classList.add('act');
  var map={t1:0,t2:1,t3:2,ta:3,t4:4};
  document.querySelectorAll('.tab')[map[id]].classList.add('act');
}
function toggle(el){el.classList.toggle('open');el.nextElementSibling.classList.toggle('open');}
var now=new Date();
document.getElementById('date').textContent=now.toLocaleDateString('en-AU',{day:'numeric',month:'short',year:'numeric'})+' '+now.toLocaleTimeString('en-AU',{hour:'2-digit',minute:'2-digit'});
</script>
</body>
</html>"""

fpath = '/Users/oc/.openclaw/workspace/index.html'
with open(fpath, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Written {len(html)} bytes")
