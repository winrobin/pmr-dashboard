#!/usr/bin/env python3
"""PMR Data Fetcher (Playwright) v18
Fixes vs v15:
  #1  MR+Unit price: parse '$2mil Business + $850k Unit = Total $2.85mil' correctly
  #2  REGIONS QLD-only + sorted longest-first so 'Surfers Paradise' beats 'SA'
  #3  fetch_onsite now visits detail page for contract/BC/price
  #4  dedup by URL + normalised name (prevents cross-source dupes)
  #5  extract_contract strips pool-unit sentences before matching
  #6  PRICE_RE extended to match $X.Xm / $X.XM shorthand
  #7  quality_score BC% logic fixed (low BC% = more letting = good)
  #8  fetch_onsite_detail added (mirrors resortbrokers detail logic)
  #9  price_drop detection vs previous JSON
"""
import json, re, traceback, os
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

OUTPUT_PATH = "/Users/oc/.openclaw/workspace/pmr/pmr-data-latest.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# FIX #2 — QLD only, sorted longest-first so 'Surfers Paradise' is checked before 'SA' never appears
REGIONS = sorted([
    "Brisbane", "Gold Coast", "Sunshine Coast", "Cairns", "Townsville", "Hervey Bay",
    "Bundaberg", "Mackay", "Rockhampton", "Toowoomba", "Noosa", "Mooloolaba",
    "Caloundra", "Gladstone", "Mudgeeraba", "Southport", "Broadbeach",
    "Surfers Paradise", "Maroochydore", "Burleigh Waters", "Burleigh Heads",
    "Robina", "Coomera", "Pimpama", "Currumbin", "Varsity Lakes",
    "Hamilton", "Carindale", "Oxley", "Albany Creek", "Griffin",
    "Ferny Grove", "Victoria Point", "Brendale", "Kangaroo Point",
    "Springwood", "Logan", "Ipswich", "Redland Bay", "Wynnum",
    "Queensland", "QLD"
], key=len, reverse=True)  # longest first prevents partial matches

NON_QLD = ["nsw","sydney","vic","melbourne","wa","perth","adelaide",
           "tas","hobart","act","canberra","nt","darwin","port macquarie","byron","tweed"]

# FIX #6 — PRICE_RE now matches $X.Xm / $X.XM shorthand
PRICE_RE   = re.compile(r'\$\s*[\d,]+(?:\.\d+)?\s*[mMkK]?')
INCOME_RE  = re.compile(r'Net\s+(?:Income|Profit)[:\s]+\$\s*([\d,]+)', re.I)
NET_SIMPLE = re.compile(r'Net[:\s]+\$\s*([\d,]+)', re.I)
BC_RE      = re.compile(r'(?:BC|Body\s+Corporate)[^\d]*\$?\s*([\d,]+)', re.I)
POOL_RE    = re.compile(r'(?:Letting\s+Pool|Pool)[^\d]*(\d+)\s*(?:units?|lots?)?', re.I)

JUNK_TITLES = ['sign up','login','log in','subscribe','contact us','enquire',
               'newsletter','click here','more information','more info',
               'view full listing','view listing','add on permanent',
               'call 0','call for','asking price','price on application',
               'id:','ref:','cooperative committee']

# ── helpers ──────────────────────────────────────────────────────────────────
def norm(t):
    return re.sub(r'[\r\n\t \xa0]+', ' ', str(t)).strip()

def parse_price(t):
    if not t: return 0
    s = norm(str(t)).lower().replace(',', '')
    m = re.search(r'\$([\d.]+)\s*m(?:il|illion)?', s)
    if m: return int(float(m.group(1)) * 1_000_000)
    m = re.search(r'\$([\d.]+)\s*k', s)
    if m: return int(float(m.group(1)) * 1_000)
    m = re.search(r'\$?\s*([\d]{3,})', s)
    return int(m.group(1)) if m else 0

def get_region(t):
    # FIX #2 — REGIONS already sorted longest-first, so Surfers Paradise checked before any 2-letter abbrev
    tl = t.lower()
    for r in REGIONS:
        if r.lower() in tl:
            return r
    return "Queensland"

def is_non_qld(t):
    import re as _re
    # Must use word boundaries so 'nt' doesn't match 'Management', 'act' doesn't match 'contract'
    pattern = r'\b(?:' + '|'.join(NON_QLD) + r')\b'
    return bool(_re.search(pattern, t, _re.I))

# FIX #1 — robust MR+Unit price extraction
def extract_total_price(text):
    """Returns (total, business_price, unit_price, is_mr_unit)"""
    t = text.lower()
    def conv(v, s):
        v = float(str(v).replace(',',''))
        s = (s or '').lower()
        if s in ('m','mil','million'): return int(v * 1_000_000)
        if s in ('k','thousand'): return int(v * 1_000)
        return int(v)
    # Pattern: "$2mil Business + $850k Unit = Total $2.850mil"
    m = re.search(r'\$([\d,\.]+)(m|mil|k)?\s*(?:business|bus)\s*\+\s*\$([\d,\.]+)(m|mil|k)?\s*unit\s*=\s*total\s*\$?([\d,\.]+)(m|mil|k)?', t)
    if m:
        biz   = conv(m.group(1), m.group(2))
        unit  = conv(m.group(3), m.group(4))
        total = conv(m.group(5), m.group(6))
        if total < biz: total = biz + unit
        return total, biz, unit, True
    # Fallback: "= Total $x.xm"
    m2 = re.search(r'=\s*total\s*\$?([\d,\.]+)(m|mil|k)?', t)
    if m2:
        total = conv(m2.group(1), m2.group(2))
        um = re.search(r'\+\s*\$([\d,\.]+)(m|mil|k)?\s*unit', t)
        unit = conv(um.group(1), um.group(2)) if um else 0
        return total, total - unit, unit, True
    return 0, 0, 0, False

def clean_name(name):
    n = name.strip()
    n = re.sub(r'^(?:Exclusive|Under\s+Contract|EXCLUSIVE|NEW LISTING|HOT|REDUCED)\s*', '', n, flags=re.I).strip()
    n = re.sub(r'\s*\$[\d,\.]+[MKmk]?.*$', '', n, flags=re.I).strip()
    for suf in ['Permanent Management Rights','Resort / Holiday Management Rights',
                'Management Rights','Business Only','Net Income',
                'VIEW FULL LISTING','VIEW LISTING','FULL LISTING',
                'Under Contract','MR & Unit','MR&Unit']:
        idx = n.lower().find(suf.lower())
        if idx > 0:
            n = n[:idx].strip().rstrip(',- ')
    n = n.strip()
    if n == n.upper() and len(n) > 3: n = n.title()
    return n[:80] if n else name[:80]

def is_junk_title(title):
    tl = title.lower().strip()
    if len(tl) < 4: return True
    return any(j in tl for j in JUNK_TITLES)

def make_listing(name, price, income, reg, url, src, bc=None, pool=None, cont=None, unit_price=0, price_drop=0):
    # FIX pool > 500
    if pool and pool > 500: pool = 0
    # FIX BC == 0
    if bc is not None and bc < 1: bc = None
    # FIX #1 — detect MR+Unit in name/text (no more ROI>35 zeroing)
    total_p, biz_p, unit_p, is_mr = extract_total_price(name)
    if is_mr and total_p > 0:
        if price == 0 or price == unit_p or price < biz_p:
            price = total_p
        if unit_price == 0: unit_price = unit_p
    name = clean_name(name)
    name = re.sub(r' \([^)]+\)', '', name).strip()
    if price and income and price == income: price = 0
    mult = round(price / income, 2) if price and income else 0
    notes, risks, action = [], [], []
    if bc:
        if bc <= 70:   notes.append(f"BC {bc}% healthy.")
        elif bc <= 80: risks.append(f"BC {bc}% — leaning caretaker.")
        else:          risks.append(f"BC {bc}% = caretaker trap. Minimal letting income.")
    if mult:
        if mult <= 5:    notes.append(f"{mult}x — excellent value.")
        elif mult <= 6.5: notes.append(f"{mult}x — fair.")
        else:            risks.append(f"{mult}x — overpriced for this income.")
    if cont:
        if cont >= 20:   notes.append(f"{cont}yr contract — very secure.")
        elif cont >= 10: notes.append(f"{cont}yr contract — adequate.")
        else:            risks.append(f"Only {cont}yr remaining — short term risk.")
    if pool and pool > 0:
        if pool >= 20:   notes.append(f"{pool} pool units — good diversification.")
        elif pool >= 10: notes.append(f"{pool} pool units.")
        else:            risks.append(f"Only {pool} pool units — small income base.")
    if price and income:
        roi = round(income / price * 100, 1)
        if roi >= 15: notes.append(f"{roi}% ROI — strong return.")
        elif roi >= 10: notes.append(f"{roi}% ROI.")
    if not notes and not risks: notes.append("Review financials before proceeding.")
    if not bc:   action.append("Request BC salary breakdown.")
    if not pool: action.append("Verify pool unit schedule.")
    if not cont: action.append("Confirm contract term remaining.")
    result = {
        "id":             src.replace('.','-') + '-' + str(abs(hash(name+url)) % 100000).zfill(5),
        "name":           name.strip(),
        "region":         reg,
        "price":          price,
        "unit_price":     unit_price,
        "net_income":     income,
        "multiplier":     mult,
        "bc_percent":     bc,
        "contract_years": cont,
        "pool_units":     pool or 0,
        "weekly_rent_per_unit": None,
        "status":         "active",
        "url":            url,
        "source":         src,
        "notes":          " ".join(notes),
        "risks":          " ".join(risks),
        "action":         " ".join(action),
        "last_updated":   datetime.now().strftime("%Y-%m-%d"),
        "last_fetched":   datetime.now().isoformat()
    }
    if price_drop > 0:
        result["price_drop"] = price_drop
    return result

def new_page(browser):
    ctx = browser.new_context(user_agent=UA, viewport={"width":1280,"height":900},
                              locale="en-AU", timezone_id="Australia/Brisbane")
    page = ctx.new_page()
    page.set_extra_http_headers({"Accept-Language":"en-AU,en;q=0.9"})
    return page

def goto(page, url, timeout=60000, extra=3000):
    try:
        page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        page.wait_for_timeout(extra)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)
        return True
    except Exception as e:
        print(f"  goto error: {e}")
        return False

# FIX #5 — strip pool sentences before contract matching
def extract_pool(t):
    m = re.search(r'Letting\s+Pool[:\s]+(\d+)', t, re.I)
    if m: return int(m.group(1))
    m = POOL_RE.search(t)
    return int(m.group(1)) if m else 0

def extract_contract(t):
    # FIX #5 — remove pool-unit sentences to avoid "27 units" → 27yr
    t_clean = re.sub(r'\d+\s*(?:units?|lots?|apartments?)[^.]*\.', '', t, flags=re.I)
    m = re.search(r'Agreement\s+Remaining[:\s]+(\d+)\s*years?', t_clean, re.I)
    if m:
        v = int(m.group(1))
        if 3 <= v <= 35: return v
    CONT_PAT = re.compile(
        r'(?:'
        r'(\d+)\s*years?\s*remaining'
        r'|(\d+)\s*years?\s*(?:remain|left)'
        r'|approximately\s+(\d+)\s*years?'
        r'|(\d+)\s*yr\s*remaining'
        r'|(?:term|agreement|module|contract)[:\s]+(?:of\s+)?(\d+)\s*years?'
        r'|(\d+)\s*years?\s*on\s+(?:the\s+)?(?:accommodation|agreement|module)'
        r')', re.I)
    m = CONT_PAT.search(t_clean)
    if m:
        val = next((g for g in m.groups() if g is not None), None)
        if val:
            v = int(val)
            if 3 <= v <= 35: return v
    return None

def extract_bc_percent(t, income):
    m = re.search(r'(?:Caretaking\s+)?Remuneration[:\s]+\$?\s*([\d,]+)', t, re.I)
    if not m: m = BC_RE.search(t)
    if m and income:
        bc_salary = parse_price('$' + m.group(1).replace(',',''))
        if bc_salary and income and bc_salary < income * 1.5:
            return round(bc_salary / income * 100, 1)
    return None

# FIX #7 — quality_score: low BC% = more letting income = better
def quality_score(p):
    score = 0
    price = p.get("price", 0) or 0
    ni    = p.get("net_income", 0) or 0
    mult  = p.get("multiplier", 0) or 0
    pool  = p.get("pool_units", 0) or 0
    cont  = p.get("contract_years") or 0
    bc    = p.get("bc_percent") or 0
    if price > 0: score += 25
    if ni > 0:    score += 25
    if mult and 3 <= mult <= 5:        score += 20
    elif mult and 5 < mult <= 6.5:     score += 10
    elif mult and mult > 8:            score -= 15
    # FIX #7: low BC% means more letting income (good), high BC% is caretaker trap
    if bc and bc <= 70:  score += 10
    elif bc and bc > 80: score -= 15
    if pool >= 20:       score += 10
    elif pool >= 10:     score += 5
    if cont and cont >= 20: score += 10
    elif cont and cont >= 10: score += 5
    if price and ni:
        roi = ni / price * 100
        if roi >= 15: score += 10
        elif roi >= 10: score += 5
    return score

def is_good_candidate(p):
    name  = p.get("name","").lower()
    price = p.get("price", 0) or 0
    ni    = p.get("net_income", 0) or 0
    mult  = p.get("multiplier", 0) or 0
    if price == 0 and ni == 0: return False
    if mult and mult > 15: return False
    if price and ni and price < ni: return False
    junk = ['caretaking only','sign up','more information','click here',
             'call 04','cooperative committee','add on permanent',
             'asking price','darwin','sale by expression','under contract'] + NON_QLD
    if any(j in name for j in junk): return False
    # FIX #2 — reject non-QLD listings
    if is_non_qld(name): return False
    return True

# ── ResortBrokers ─────────────────────────────────────────────────────────────
def fetch_resortbrokers_detail(browser, href, name):
    page = new_page(browser)
    try:
        if not goto(page, href, timeout=30000, extra=2000): return 0, None, None, None
        t = norm(page.inner_text("body"))
        # MR+Unit detection on detail page
        total_p, biz_p, unit_p, is_mr = extract_total_price(t)
        if is_mr and total_p > 0:
            price = total_p
        else:
            pm = re.search(r'(?:PRICE|Asking Price)[:\s\n]+\$?\s*([\d,]+)', t, re.I)
            price = parse_price('$' + pm.group(1)) if pm else 0
            if not price:
                ni_m = re.search(r'NET\s+PROFIT[:\s\n]+\$?\s*([\d,]+)', t, re.I)
                ni_v = parse_price('$' + ni_m.group(1)) if ni_m else 0
                all_prices = [parse_price(m.group(0)) for m in PRICE_RE.finditer(t)]
                candidates = [p for p in all_prices if p > ni_v and p > 200000]
                price = max(candidates) if candidates else 0
        pool = extract_pool(t)
        cont = extract_contract(t)
        ni_m2 = re.search(r'NET\s+PROFIT[:\s\n]+\$?\s*([\d,]+)', t, re.I)
        ni_detail = parse_price('$' + ni_m2.group(1)) if ni_m2 else 0
        bc = extract_bc_percent(t, ni_detail)
        return price, bc, pool, cont
    except Exception as e:
        print(f"  detail error ({name[:30]}): {e}")
        return 0, None, None, None
    finally:
        page.context.close()

def fetch_resortbrokers(browser):
    src, base = "resortbrokers.com.au", "https://www.resortbrokers.com.au"
    url = base + "/management-rights-for-sale/"
    page, out = new_page(browser), []
    try:
        if not goto(page, url): return out
        cards = page.query_selector_all("div.listing-flex-item")
        if not cards: cards = page.query_selector_all("article.property-card")
        print(f"  Found {len(cards)} cards")
        for i, card in enumerate(cards):
            try:
                t = norm(card.inner_text())
                if not t or len(t) < 10: continue
                if is_non_qld(t): continue
                net_el = card.query_selector("p.price")
                net_text = norm(net_el.inner_text()) if net_el else ""
                ni_m = NET_SIMPLE.search(net_text) or PRICE_RE.search(net_text)
                if isinstance(ni_m, re.Match) and ni_m.lastindex:
                    income = parse_price(ni_m.group(1))
                else:
                    income = parse_price(ni_m.group(0)) if ni_m else 0
                title_el = card.query_selector("h2,h3,.listing-title")
                raw_title = norm(title_el.inner_text()) if title_el else t[:80]
                raw_title = re.sub(r'^[A-Z]{2,}\d{5,}\s*', '', raw_title).strip()
                for ph in ['EXCLUSIVE ','MANAGEMENT RIGHTS ','BUSINESS ONLY ','OFF THE PLAN ','VIEW FULL LISTING']:
                    raw_title = raw_title.replace(ph,'').strip()
                m = re.search(r'^(.+?),?\s*(QLD|NSW|VIC|WA|SA|NT|ACT|TAS)\b', raw_title)
                title = (m.group(1).strip().title() + ' ' + m.group(2)) if m else raw_title.title()[:80]
                if is_junk_title(title): continue
                link = card.query_selector("a[href]")
                href = link.get_attribute("href") if link else url
                if href and not href.startswith("http"): href = base + href
                import time, random
                print(f"  [{i+1}] {title[:40]} — fetching detail...")
                time.sleep(random.uniform(0.5, 1.5)) # Anti-bot delay
                price, bc, pool, cont = fetch_resortbrokers_detail(browser, href, title)
                if income == 0 and price == 0: continue
                if price and income and price == income: price = 0
                out.append(make_listing(title, price, income, get_region(t), href, src, bc, pool, cont))
            except Exception as e:
                print(f"  card {i} error: {e}")
    except Exception as e:
        print(f"  {src} error: {e}")
    finally:
        page.context.close()
    return out

# ── AccomProperties ───────────────────────────────────────────────────────────
def fetch_accom(browser):
    src, base = "accomproperties.com.au", "https://accomproperties.com.au"
    url = base + "/management-rights-for-sale"
    page, out = new_page(browser), []
    try:
        if not goto(page, url): return out
        cards = page.query_selector_all("div.property-item")
        print(f"  Found {len(cards)} cards")
        for i, card in enumerate(cards):
            try:
                t = norm(card.inner_text())
                if is_non_qld(t): continue
                link = card.query_selector("a[href]")
                href = link.get_attribute("href") if link else url
                if href and not href.startswith("http"): href = base + href
                price_el = card.query_selector(".price,.asking-price")
                price = parse_price(price_el.inner_text()) if price_el else 0
                im = INCOME_RE.search(t)
                income = parse_price(im.group(1)) if im else 0
                if not price:
                    all_p = [parse_price(m.group(0)) for m in PRICE_RE.finditer(t) if parse_price(m.group(0)) > 0]
                    cands = [p for p in all_p if p > income] if income else all_p
                    price = max(cands) if cands else 0
                    if price == income: price = 0
                title_el = card.query_selector("h2,h3,.property-title,.listing-title")
                title = norm(title_el.inner_text()) if title_el else t[:60]
                title = clean_name(title)
                if is_junk_title(title): continue
                pool = extract_pool(t)
                cont = extract_contract(t)
                bc = extract_bc_percent(t, income)
                if href and href != url:
                    import time, random
                    time.sleep(random.uniform(0.5, 1.5)) # Anti-bot delay
                    dp = new_page(browser)
                    try:
                        if goto(dp, href, timeout=30000, extra=2000):
                            dt = norm(dp.inner_text("body"))
                            # MR+Unit detection on detail page
                            total_p, biz_p, unit_p, is_mr = extract_total_price(dt)
                            if is_mr and total_p > 0:
                                price = total_p
                            else:
                                cont2 = extract_contract(dt)
                                if cont2: cont = cont2
                                im2 = INCOME_RE.search(dt)
                                inc2 = parse_price(im2.group(1)) if im2 else 0
                                if inc2 > 0: income = inc2
                                pm = re.search(r'(?:Asking\s+)?Price[:\s]+\$?\s*([\d,]+)', dt, re.I)
                                if pm:
                                    price = parse_price('$' + pm.group(1))
                                elif not price or price == income:
                                    all_p2 = [parse_price(m.group(0)) for m in PRICE_RE.finditer(dt) if parse_price(m.group(0)) > 0]
                                    cands2 = [p2 for p2 in all_p2 if p2 > (income or 0) and p2 < 15_000_000]
                                    if cands2: price = max(cands2)
                            bc2 = extract_bc_percent(dt, income)
                            if bc2: bc = bc2
                            pool2 = extract_pool(dt)
                            if pool2: pool = pool2
                    except: pass
                    finally: dp.context.close()
                if price and income and price == income: price = 0
                if (price > 0 or income > 0) and title:
                    out.append(make_listing(title, price, income, get_region(t), href, src, bc, pool, cont))
            except Exception as e:
                print(f"  card {i} error: {e}")
    except Exception as e:
        print(f"  {src} error: {e}")
    finally:
        page.context.close()
    return out

# FIX #8 — fetch_onsite_detail (new)
def fetch_onsite_detail(browser, href, income):
    page = new_page(browser)
    try:
        if not goto(page, href, timeout=30000, extra=2000): return 0, None, None, None, 0
        t = norm(page.inner_text("body"))
        # MR+Unit detection
        total_p, biz_p, unit_p, is_mr = extract_total_price(t)
        if is_mr and total_p > 0:
            price = total_p
        else:
            pm = re.search(r'(?:Asking\s+)?Price[:\s\n]+\$?\s*([\d,]+)', t, re.I)
            price = parse_price('$' + pm.group(1)) if pm else 0
            if not price:
                all_p = [parse_price(m.group(0)) for m in PRICE_RE.finditer(t)]
                cands = [p for p in all_p if p > (income or 0) and p > 200000 and p < 15_000_000]
                price = max(cands) if cands else 0
        pool = extract_pool(t)
        cont = extract_contract(t)
        # BC% — prefer Remuneration field on detail page
        im2 = INCOME_RE.search(t)
        ni2 = parse_price(im2.group(1)) if im2 else income
        bc = extract_bc_percent(t, ni2 or income)
        unit_price = unit_p if is_mr else 0
        return price, bc, pool, cont, unit_price
    except Exception as e:
        print(f"  onsite detail error: {e}")
        return 0, None, None, None, 0
    finally:
        page.context.close()

# ── TheOnsiteManager (FIX #3 + #8 — now visits detail page) ──────────────────
def fetch_onsite(browser):
    src, base = "theonsitemanager.com.au", "https://www.theonsitemanager.com.au"
    url = base + "/management-rights"
    page, out = new_page(browser), []
    try:
        if not goto(page, url): return out
        cards = page.query_selector_all("div.pgl-property")
        print(f"  Found {len(cards)} cards")
        for i, card in enumerate(cards):
            try:
                t = norm(card.inner_text())
                if is_non_qld(t): continue
                link = card.query_selector("a[href]")
                href = link.get_attribute("href") if link else url
                if href and not href.startswith("http"): href = base + href
                im = INCOME_RE.search(t)
                income = parse_price(im.group(1)) if im else 0
                if not income:
                    rem = re.search(r'Remuneration[:\s]+\$\s*([\d,]+)', t, re.I)
                    income = parse_price(rem.group(1)) if rem else 0
                # MR+Unit on card text first
                total_p, biz_p, unit_p, is_mr = extract_total_price(t)
                if is_mr and total_p > 0:
                    price = total_p
                else:
                    all_p = [parse_price(m.group(0)) for m in PRICE_RE.finditer(t) if parse_price(m.group(0)) > 0]
                    cands = [p for p in all_p if p > income] if income else all_p
                    price = max(cands) if cands else 0
                    if price == income and income > 0: price = 0
                lines = [l.strip() for l in t.split('  ') if l.strip() and not l.strip().startswith('$')]
                title = lines[0][:100] if lines else t[:60]
                title = clean_name(title)
                if is_junk_title(title): continue
                pool = extract_pool(t)
                cont = extract_contract(t)
                bc   = extract_bc_percent(t, income)
                import time, random
                # FIX #3 + #8 — visit detail page to fill missing fields
                if href and href != url:
                    time.sleep(random.uniform(0.5, 1.5)) # Prevent rate-limiting / heavy context creation
                    det_price, det_bc, det_pool, det_cont, det_unit = fetch_onsite_detail(browser, href, income)
                    if det_price > 0 and det_price != income and det_price > price: price = det_price
                    if det_bc is not None: bc = det_bc
                    if det_pool: pool = det_pool
                    if det_cont: cont = det_cont
                    unit_price = det_unit
                else:
                    unit_price = unit_p if is_mr else 0
                if price > 100000 and title:
                    out.append(make_listing(title, price, income, get_region(t), href, src, bc, pool, cont, unit_price=unit_price))
            except Exception as e:
                print(f"  card {i} error: {e}")
    except Exception as e:
        print(f"  {src} error: {e}")
    finally:
        page.context.close()
    return out

# ── SIRE ──────────────────────────────────────────────────────────────────────
def fetch_sire(browser):
    src, base = "siremanagementrights.com.au", "https://siremanagementrights.com.au"
    url = base + "/management-rights-for-sale"
    page, out = new_page(browser), []
    JUNK = ['click here','more information','sign up','log in','login','subscribe',
            'contact us','enquire','newsletter','add on permanent','asking price','call 04']
    try:
        if not goto(page, url, timeout=45000, extra=3000): return out
        full = norm(page.inner_text("body"))
        blocks = re.split(r'\n{2,}| {3,}', full)
        for block in blocks:
            block = norm(block)
            if len(block) < 30: continue
            if is_non_qld(block): continue
            if not any(k in block.lower() for k in ["management rights","letting pool","net income","remuneration"]): continue
            first_line = block.split('.')[0].lower().strip()
            if any(j in first_line for j in JUNK): continue
            im = INCOME_RE.search(block)
            income = parse_price(im.group(1)) if im else 0
            total_p, biz_p, unit_p, is_mr = extract_total_price(block)
            if is_mr and total_p > 0:
                price = total_p
            else:
                all_p = [parse_price(m.group(0)) for m in PRICE_RE.finditer(block) if parse_price(m.group(0)) > 0]
                cands = [p for p in all_p if p > income] if income > 0 else all_p
                price = max(cands) if cands else 0
                if price == income and income > 0: price = 0
            title = ""
            for line in block.split("  "):
                l = line.strip()
                if len(l) < 8: continue
                if re.search(r'\d{4}\s*\d{3}\s*\d{3}|0[45]\d{8}', l): continue
                if re.search(r'http|www\.', l): continue
                if any(j in l.lower() for j in JUNK): continue
                title = l[:120]; break
            if not title: title = block[:80].split('.')[0]
            title = clean_name(title)
            if is_junk_title(title): continue
            pool = extract_pool(block)
            cont = extract_contract(block)
            bc = extract_bc_percent(block, income)
            if price > 100000 and title.strip():
                out.append(make_listing(title, price, income, get_region(block), url, src, bc, pool, cont))
    except Exception as e:
        print(f"  {src} error: {e}")
    finally:
        page.context.close()
    return out

# ── BusinessForSale ───────────────────────────────────────────────────────────
def fetch_bfs(browser):
    src, base = "businessforsale.com.au", "https://www.businessforsale.com.au"
    url = base + "/businesses-for-sale/management-rights/qld"
    page, out = new_page(browser), []
    try:
        if not goto(page, url, timeout=30000): return out
        cards = page.query_selector_all("div.listing-item,div.business-card,article")
        print(f"  Found {len(cards)} cards")
        for i, card in enumerate(cards):
            try:
                t = norm(card.inner_text())
                if "management rights" not in t.lower(): continue
                if is_non_qld(t): continue
                link = card.query_selector("a[href]")
                href = link.get_attribute("href") if link else url
                if href and not href.startswith("http"): href = base + href
                im = INCOME_RE.search(t)
                income = parse_price(im.group(1)) if im else 0
                all_p = [parse_price(m.group(0)) for m in PRICE_RE.finditer(t) if parse_price(m.group(0)) > 0]
                cands = [p for p in all_p if p > income] if income else all_p
                price = max(cands) if cands else 0
                if price == income and income > 0: price = 0
                title_el = card.query_selector("h2,h3,.listing-title")
                title = clean_name(norm(title_el.inner_text()) if title_el else t[:60])
                if is_junk_title(title): continue
                if price > 100000 and title:
                    out.append(make_listing(title, price, income, get_region(t), href, src))
            except Exception as e:
                print(f"  card {i} error: {e}")
    except Exception as e:
        print(f"  {src} error: {e}")
    finally:
        page.context.close()
    return out

# FIX #4 — dedup by URL + normalised name
def dedup(items):
    seen_urls, seen_names, out, n = set(), {}, [], 0
    for item in items:
        url_key  = item.get("url","").split("?")[0].lower().strip("/")
        name_key = re.sub(r'\s+',' ', item["name"].lower().strip())[:50]
        if url_key and url_key in seen_urls:
            n += 1; continue
        if name_key in seen_names:
            n += 1; continue
        if url_key:  seen_urls.add(url_key)
        seen_names[name_key] = True
        out.append(item)
    return out, n

def apply_quality_filter(items, target=50):
    good = [p for p in items if is_good_candidate(p)]
    removed_hard = len(items) - len(good)
    scored = sorted(good, key=quality_score, reverse=True)
    full_data = [p for p in scored if p.get("price",0) > 0 and p.get("net_income",0) > 0]
    partial   = [p for p in scored if p not in full_data]
    final = full_data[:target]
    remaining = target - len(final)
    if remaining > 0: final += partial[:remaining]
    return final, removed_hard, len(items) - len(final)

# FIX #9 — price drop detection
def detect_price_drops(new_items, output_path):
    if not os.path.exists(output_path): return new_items
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            old_data = json.load(f)
        old_by_url = {p["url"].split("?")[0].lower().strip("/"): p for p in old_data if p.get("url")}
        for item in new_items:
            url_key = item.get("url","").split("?")[0].lower().strip("/")
            old = old_by_url.get(url_key)
            if old:
                old_price = old.get("price", 0) or 0
                new_price = item.get("price", 0) or 0
                if old_price > 0 and new_price > 0 and old_price > new_price:
                    drop = old_price - new_price
                    item["price_drop"] = drop
                    print(f"  💰 Price drop: {item['name']} ${drop:,.0f}")
    except Exception as e:
        print(f"  price_drop detection error: {e}")
    return new_items

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    print("PMR Data Fetcher (Playwright) v18 Starting...")
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S\n"))
    fetchers = [
        ("accomproperties.com.au",      fetch_accom),
        ("resortbrokers.com.au",         fetch_resortbrokers),
        ("theonsitemanager.com.au",      fetch_onsite),
        ("siremanagementrights.com.au",  fetch_sire),
        ("businessforsale.com.au",       fetch_bfs),
    ]
    all_items, summary = [], {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-blink-features=AutomationControlled"]
        )
        for name, fn in fetchers:
            print(f"▶ {name}")
            try:
                results = fn(browser)
                print(f"  -> {len(results)} listings")
                summary[name] = ("OK" if results else "--", len(results))
                all_items.extend(results)
            except Exception as e:
                print(f"  -> ERROR: {e}")
                summary[name] = ("ERR", 0)
        browser.close()
    unique, dupes = dedup(all_items)
    final, hard_removed, soft_removed = apply_quality_filter(unique, target=50)
    # FIX #9
    final = detect_price_drops(final, OUTPUT_PATH)
    print("\nSource Summary:")
    for n,(status,c) in summary.items():
        print(f"  {status} {n}: {c} listings")
    print(f"  Removed {dupes} duplicates")
    print(f"  Removed {hard_removed} junk/invalid listings")
    print(f"  Kept top {len(final)} quality candidates\n")
    if not final:
        print("WARNING: No listings found. JSON not updated.")
        return
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)
    tv  = sum(l["price"] for l in final)
    ti  = sum(l["net_income"] for l in final)
    avg = round(tv / ti, 2) if ti else 0
    drops = [l for l in final if l.get("price_drop",0) > 0]
    print(f"Saved {len(final)} listings to {OUTPUT_PATH}")
    print(f"Total value: ${tv:,.0f}")
    print(f"Total net income: ${ti:,.0f}")
    print(f"Avg multiplier: {avg}x")
    if drops:
        print(f"\n💰 Price drops detected: {len(drops)}")
        for d in drops:
            print(f"  {d['name']} — dropped ${d['price_drop']:,.0f}")
    print("\nDone!")

if __name__ == "__main__":
    main()
