#!/usr/bin/env python3
import json, re

with open('/Users/oc/.openclaw/workspace/index.html') as f:
    h = f.read()

cards = []

# Parse all property cards from the HTML
# Pattern: find each card div with data
card_pattern = re.compile(r'class="pc".*?class="rk ([^"]+)".*?nm">(.*?)</span>.*?href="([^"]*)".*?<div class="sub">(.*?)</div>.*?<div class="am">(.*?)</div>.*?<div class="l">NetInc</div></div><div class="v ([^"]+)".*?<div class="l">BC%</div></div><div class="v ([^"]+)".*?<div class="l">Lett</div></div><div class="v ([^"]+)".*?<div class="l">Mult</div></div><div class="v ([^"]+)".*?<div class="l">Pool</div></div><div class="v ([^"]+)".*?<div class="l">Cont</div></div><div class="v ([^"]+)"', re.DOTALL)

for m in card_pattern.finditer(h):
    cls, name, url, sub, price, ni, bcp, lett, mult, pool, cont = m.groups()
    
    # Extract notes and risks
    notes_section = re.search(r'class="rb">(.*?)</div>', m.group(0), re.DOTALL)
    notes = notes_section.group(1) if notes_section else ""
    
    cards.append({
        "class": cls,
        "name": name.strip(),
        "url": url,
        "sub": sub.strip(),
        "price": price.strip(),
        "net_income": ni.strip(),
        "bc_percent": bcp.strip(),
        "letting_income": lett.strip(),
        "multiplier": mult.strip(),
        "pool": pool.strip(),
        "contract_years": cont.strip(),
    })

# Extract action items
for i, card in enumerate(cards):
    # Find the action div for this card
    start = h.find(card["url"])
    if start > 0:
        action_match = re.search(r'class="ax">.*?<b>(.*?)</b></div>', h[start:], re.DOTALL)
        if action_match:
            cards[i]["action_raw"] = action_match.group(1).strip()

with open('/Users/oc/.openclaw/workspace/pmr-data-latest.json', 'w') as f:
    json.dump(cards, f, indent=2, ensure_ascii=False)

print(f"Exported {len(cards)} properties to pmr-data-latest.json")
for c in cards:
    print(f"  {c['name']}: {c['price']} | {c['net_income']} | BC% {c['bc_percent']} | {y['contract_years']}")
