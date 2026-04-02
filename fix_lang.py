import os

fpath = '/Users/oc/.openclaw/workspace/index.html'
with open(fpath, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add CSS for lang button
css_block = '.lng-btn{position:fixed;top:8px;right:8px;z-index:200;background:#1d4ed8;color:#fff;border:none;font-size:11px;font-weight:bold;padding:7px 12px;border-radius:6px;cursor:pointer;opacity:0.95}.lng-btn:hover{opacity:1}'
html = html.replace('<style>', '<style>\n' + css_block, 1)

# 2. Add lang button at top of body
html = html.replace('<body>', '<body>\n<button class="lng-btn" onclick="toggleLang()">EN</button>')

# 3. Add padding to hd so button doesnt overlap
html = html.replace('.hd{background:#111827;padding:14px 10px;', '.hd{background:#111827;padding:14px 10px;padding-right:70px;')

# 4. Add data-zh attributes to guide section headings
guide_items = [
    ('1. What is PMR?', '1. 什么是PMR？'),
    ('2. Key Terms', '2. 关键术语'),
    ('3. How to Evaluate a PMR Deal', '3. 如何评估PMR交易'),
    ('4. Financial Analysis', '4. 财务分析'),
    ('5. Legal & Regulatory', '5. 法律与监管'),
    ('6. Market Overview — Brisbane & Gold Coast', '6. 市场概况'),
    ('7. Buying Process — Step by Step', '7. 购买流程'),
    ('8. Common Pitfalls & Red Flags', '8. 红旗警告'),
    ('9. Resources & Further Reading', '9. 资源'),
]
for en, zh in guide_items:
    if en + '</span>' in html:
        html = html.replace(en + '</span>', zh + '</span>', 1)

# Also update legend labels
html = html.replace('ABBREVIATIONS LEGEND', '缩写说明')
html = html.replace('= Body Corp Salary % ', '= Body Corp薪资占比 ')
html = html.replace('= Commission per unit per week ', '= 每单元周佣金 ')
html = html.replace('= Price / Net Income ', '= 价格/净收入 ')
html = html.replace('= Units in letting pool', '= Letting Pool单元数')
html = html.replace('= Contract years remaining', '= 合同年限')

# 5. Add toggleLang function before the closing script tag
toggle_js = '''
var lang='en';
function toggleLang(){
  lang=(lang==='en')?'zh':'en';
  var btn=document.querySelector('.lng-btn');
  btn.textContent=(lang==='zh')?'中文':'EN';
  if(lang==='zh'){
    document.getElementById('sub').textContent='布里斯班 + 黄金海岸 | 20 物业 | 3个档位';
    document.getElementById('leg_h').textContent='缩写说明';
    document.getElementById('leg1').textContent='= Body Corp薪资占比 (理想60-70%,>80%=风险)';
    document.getElementById('leg2').textContent='= 每单元周佣金 (正常$60-85)';
    document.getElementById('leg3').textContent='= 价格/净收入 (越低越好,理想3-5x)';
    document.getElementById('leg4').textContent='= Letting Pool单元数';
    document.getElementById('leg5').textContent='= 合同年限';
    document.getElementById('leg_g').textContent='🟢=良好';
    document.getElementById('leg_y').textContent='🟡=注意';
    document.getElementById('leg_r').textContent='🔴=风险';
    document.getElementById('tab1').textContent='第1档';
    document.getElementById('tab2').textContent='第2档';
    document.getElementById('tab3').textContent='第3档';
    document.getElementById('taba').textContent='全部';
    document.getElementById('tab4').textContent='指南';
    document.getElementById('foot').textContent='通过GitHub Pages自动更新';
  } else {
    document.getElementById('sub').textContent='Brisbane + Gold Coast | 20 Properties | 3 Tiers';
    document.getElementById('leg_h').textContent='ABBREVIATIONS LEGEND';
    document.getElementById('leg1').textContent='= Body Corp Salary % (ideal 60-70%, >80% = risk)';
    document.getElementById('leg2').textContent='= Commission per unit per week (normal $60-85)';
    document.getElementById('leg3').textContent='= Price / Net Income multiplier (lower = better, ideal 3-5x)';
    document.getElementById('leg4').textContent='= Units in letting pool';
    document.getElementById('leg5').textContent='= Contract years remaining';
    document.getElementById('leg_g').textContent='🟢 = Good / Healthy';
    document.getElementById('leg_y').textContent='🟡 = Acceptable / Caution';
    document.getElementById('leg_r').textContent='🔴 = Risk / Problem';
    document.getElementById('tab1').textContent='Tier 1 (13)';
    document.getElementById('tab2').textContent='Tier 2 (3)';
    document.getElementById('tab3').textContent='Tier 3 (4)';
    document.getElementById('taba').textContent='All';
    document.getElementById('tab4').textContent='Guide';
    document.getElementById('foot').textContent='Auto-updated via GitHub Pages';
  }
}
'''

html = html.replace('<script>\n', '<script>\n' + toggle_js)

with open(fpath, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Updated. File size: {len(html)} bytes")
