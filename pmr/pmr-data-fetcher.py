#!/usr/bin/env python3
"""PMR Data Fetcher (Playwright) v29
Changes vs v28:
#22 onsite pricing: prefer detail Total Purchase Price, then card headline price, then business+unit
#22 onsite pricing: any card with Manager's Estate / Included Real Estate / headline price triggers detail verification
#22 add price_source field so JSON shows where each price came from

Changes vs v27:
#21 quality_score: Brisbane south / Eight Mile Plains corridor location bonus
#21 weight nearby suburbs: Eight Mile Plains +12; nearby ring suburbs +8
#21 goal: keep strong South Brisbane / EMP corridor listings (e.g. Eight Mile Plains, Runcorn) in top-80
#20 apply_quality_filter: stamp quality_score into each listing dict

Changes vs v25:
#17 main: top-N target 50 → 80 — restores $1.5M listings displaced by FIX #16 high-income priority
#18 REGIONS: added 30+ Gold Coast suburbs → fixes GC listings misclassified as Brisbane
#18 get_region: suburb-first matching on card URL/title before scanning full card text
#19 fetch_onsite: high-income listings (ni>=400k) always fetch detail page for true total price
     → Eight Mile Plains: card shows business-only $4.26M; detail page has Total Purchase Price $5.97M

Changes vs v23:
#10 fetch_onsite: new Angular SPA selector (app-listing-card, April 2026 platform relaunch)
#10 fetch_onsite: reads .mr-row/.mr-label/.mr-val for income/remuneration/multiplier
#10 fetch_onsite: wait_for_selector ensures Angular render complete
#11 fetch_onsite: title from .card-location suburb (not generic .card-title type label)
#11 fetch_onsite: pagination via .pagination button:last-child:not([disabled])
#11 fetch_onsite: 18 pages × 24 cards = ~416 listings total
#12 fetch_onsite: title = suburb + card_id → unique, fixes dedup false-positives
#13 fetch_onsite: skip detail page visits → 18 pages in ~90s not 20 min
#14 dedup: add (price,income,region) fingerprint → catches same property listed by multiple brokers
#15 fetch_onsite_detail: "Total Purchase Price / Purchase Price" regex fallback for undisclosed multiplier
#15 fetch_onsite: calc multiplier = price/income when site hides it
#16 quality_score: high net income bonus — ni>=500k:+15, ni>=300k:+8, ni>=150k:+4
#16 apply_quality_filter: high-income listings (net_income>=500k) always included,
     exempt from top-N cutoff regardless of multiplier penalty
     → Eight Mile Plains ($664k income, 8.97x, 71 units, 20yr) now always in output
"""
import json, re, traceback, os, time, random
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

OUTPUT_PATH = "/Users/oc/.openclaw/workspace/pmr/pmr-data-latest.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# FIX #2 — QLD only, sorted longest-first so 'Surfers Paradise' is checked before 'SA' never appears
REGIONS = sorted([
# Brisbane suburbs
"Brisbane", "Kangaroo Point", "Kangaroo Point", "New Farm", "West End",
"South Brisbane", "Fortitude Valley", "Teneriffe", "Newstead", "Bulimba",
"Hamilton", "Ascot", "Eagle Farm", "Carindale", "Oxley", "Albany Creek",
"Griffin", "Ferny Grove", "Victoria Point", "Brendale", "Springwood",
"Logan", "Ipswich", "Redland Bay", "Wynnum", "Eight Mile Plains",
"Upper Mount Gravatt", "Mount Gravatt", "Sunnybank", "Sunnybank Hills",
"Mansfield", "Rochedale", "Underwood", "Slacks Creek", "Loganholme",
"Meadowbrook", "Daisy Hill", "Shailer Park", "Tanah Merah",
"Capalaba", "Cleveland", "Alexandra Hills", "Birkdale", "Wellington Point",
# Gold Coast suburbs — FIX #18
"Gold Coast", "Surfers Paradise", "Broadbeach", "Broadbeach Waters",
"Southport", "Robina", "Varsity Lakes", "Burleigh Heads", "Burleigh Waters",
"Mudgeeraba", "Currumbin", "Currumbin Waters", "Palm Beach", "Tugun",
"Coolangatta", "Tweed Heads", "Bilinga", "Kirra", "Cabarita Beach",
"Nerang", "Carrara", "Merrimac", "Worongary", "Tallai", "Advancetown",
"Helensvale", "Oxenford", "Hope Island", "Sanctuary Cove", "Runaway Bay",
"Labrador", "Biggera Waters", "Hollywell", "Paradise Point", "Coombabah",
"Coomera", "Upper Coomera", "Pimpama", "Ormeau", "Yatala",
"Mudgeeraba", "Bonogin", "Reedy Creek", "Elanora", "Tallebudgera",
"Mermaid Beach", "Mermaid Waters", "Clear Island Waters", "Miami",
"Nobby Beach", "Benowa", "Parkwood", "Molendinar", "Arundel",
"Ashmore", "Highland Park", "Gaven", "Gilston", "Mount Nathan",
"Tamborine Mountain", "Canungra", "Beaudesert",
# Sunshine Coast suburbs
"Sunshine Coast", "Noosa", "Noosaville", "Noosa Heads", "Tewantin",
"Mooloolaba", "Maroochydore", "Caloundra", "Kawana Waters", "Bokarina",
"Buddina", "Warana", "Wurtulla", "Birtinya", "Sippy Downs",
"Buderim", "Nambour", "Coolum Beach", "Peregian Beach", "Sunrise Beach",
"Mount Coolum", "Marcoola", "Bli Bli", "Yandina", "Eumundi",
"Pomona", "Cooroy", "Tin Can Bay", "Rainbow Beach",
# Regional QLD
"Cairns", "Townsville", "Hervey Bay", "Bundaberg", "Mackay",
"Rockhampton", "Toowoomba", "Gladstone", "Emerald", "Longreach",
"Mount Isa", "Charleville", "Roma", "Dalby", "Warwick", "Stanthorpe",
"Queensland", "QLD"
], key=len, reverse=True)

NON_QLD = ["nsw","sydney","vic","melbourne","wa","perth","adelaide",
"tas","hobart","act","canberra","nt","darwin","port macquarie","byron","tweed"]

PRICE_RE = re.compile(r'\$\s*[\d,]+(?:\.\d+)?\s*[mMkK]?')
INCOME_RE = re.compile(r'Net\s+(?:Income|Profit)[:\s]+\$\s*([\d,]+)', re.I)
NET_SIMPLE = re.compile(r'Net[:\s]+\$\s*([\d,]+)', re.I)
BC_RE = re.compile(r'(?:BC|Body\s+Corporate)[^\d]*\$?\s*([\d,]+)', re.I)
POOL_RE = re.compile(r'(?:Letting\s+Pool|Pool)[^\d]*(\d+)\s*(?:units?|lots?)?', re.I)

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

# FIX #18 — Gold Coast suburb map: any suburb in this set → "Gold Coast"
GOLD_COAST_SUBURBS = {
    "surfers paradise","broadbeach","broadbeach waters","southport","robina",
    "varsity lakes","burleigh heads","burleigh waters","mudgeeraba","currumbin",
    "currumbin waters","palm beach","tugun","coolangatta","bilinga","kirra",
    "nerang","carrara","merrimac","worongary","helensvale","oxenford",
    "hope island","sanctuary cove","runaway bay","labrador","biggera waters",
    "hollywell","paradise point","coombabah","coomera","upper coomera",
    "pimpama","ormeau","reedy creek","elanora","tallebudgera","mermaid beach",
    "mermaid waters","clear island waters","miami","nobby beach","benowa",
    "parkwood","molendinar","arundel","ashmore","highland park","gaven","gilston",
}

BRISBANE_SUBURBS = {
    "kangaroo point","new farm","west end","south brisbane","fortitude valley",
    "teneriffe","newstead","bulimba","hamilton","ascot","eagle farm","carindale",
    "oxley","springwood","eight mile plains","upper mount gravatt","mount gravatt",
    "sunnybank","sunnybank hills","mansfield","rochedale","underwood","loganholme",
    "capalaba","cleveland","birkdale","wellington point","wynnum","redland bay",
    "albany creek","griffin","ferny grove","brendale","victoria point",
}

# FIX #21 — Eight Mile Plains corridor weighting for South Brisbane investment belt
EMP_RING_SUBURBS = {
    "runcorn", "rochedale", "rochedale south", "underwood", "upper mount gravatt",
    "wishart", "sunnybank", "sunnybank hills", "stretton", "kuraby",
    "macgregor", "robertson"
}

def get_region(t):
    # FIX #18 — check URL slug and first 120 chars (title/suburb) BEFORE full text
    # This prevents footer/nav "Brisbane" text from overriding a GC suburb title
    tl_short = t.lower()[:120]
    for sub in GOLD_COAST_SUBURBS:
        if sub in tl_short:
            return "Gold Coast"
    for sub in BRISBANE_SUBURBS:
        if sub in tl_short:
            return "Brisbane"
    # Fallback: scan full text with REGIONS list
    tl = t.lower()
    for r in REGIONS:
        if r.lower() in tl:
            return r
    return "Queensland"

def is_non_qld(t):
    pattern = r'\b(?:' + '|'.join(NON_QLD) + r')\b'
    return bool(re.search(pattern, t, re.I))

def extract_total_price(text):
    """Returns (total, business_price, unit_price, is_mr_unit)"""
    t = text.lower()
    def conv(v, s):
        v = float(str(v).replace(',',''))
        s = (s or '').lower()
        if s in ('m','mil','million'): return int(v * 1_000_000)
        if s in ('k','thousand'): return int(v * 1_000)
        return int(v)
    m = re.search(r'\$([\d,\.]+)(m|mil|k)?\s*(?:business|bus)\s*\+\s*\$([\d,\.]+)(m|mil|k)?\s*unit\s*=\s*total\s*\$?([\d,\.]+)(m|mil|k)?', t)
    if m:
        biz = conv(m.group(1), m.group(2))
        unit = conv(m.group(3), m.group(4))
        total = conv(m.group(5), m.group(6))
        if total < biz: total = biz + unit
        return total, biz, unit, True
    m2 = re.search(r'=\s*total\s*\$?([\d,\.]+)(m|mil|k)?', t)
    if m2:
        total = conv(m2.group(1), m2.group(2))
        um = re.search(r'\+\s*\$([\d,\.]+)(m|mil|k)?\s*unit', t)
        unit = conv(um.group(1), um.group(2)) if um else 0
        return total, total - unit, unit, True
    return 0, 0, 0, False

def extract_card_headline_price(card):
    """Read the prominent card headline price from Onsite card DOM."""
    selectors = [
        ".card-price", ".price", ".listing-price", ".headline-price",
        ".price-wrapper", ".property-price"
    ]
    best = 0
    for sel in selectors:
        try:
            els = card.query_selector_all(sel)
        except Exception:
            els = []
        for el in els or []:
            try:
                txt = norm(el.inner_text())
            except Exception:
                continue
            p = parse_price(txt)
            if p > best:
                best = p
    if best > 100000:
        return best
    try:
        all_text = norm(card.inner_text())
    except Exception:
        all_text = ""
    prices = [parse_price(m.group(0)) for m in PRICE_RE.finditer(all_text)]
    prices = [p for p in prices if 100000 < p < 15000000]
    return max(prices) if prices else 0


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
            n = n[:idx].strip().rstrip(',-  ')
    n = n.strip()
    if n == n.upper() and len(n) > 3: n = n.title()
    return n[:80] if n else name[:80]

def is_junk_title(title):
    tl = title.lower().strip()
    if len(tl) < 4: return True
    return any(j in tl for j in JUNK_TITLES)

def make_listing(name, price, income, reg, url, src, bc=None, pool=None, cont=None, unit_price=0, price_drop=0, price_source=None):
    if pool and pool > 500: pool = 0
    if bc is not None and bc < 1: bc = None
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
        if bc <= 70: notes.append(f"BC {bc}% healthy.")
        elif bc <= 80: risks.append(f"BC {bc}% — leaning caretaker.")
        else: risks.append(f"BC {bc}% = caretaker trap. Minimal letting income.")
    if mult:
        if mult <= 5: notes.append(f"{mult}x — excellent value.")
        elif mult <= 6.5: notes.append(f"{mult}x — fair.")
        else: risks.append(f"{mult}x — overpriced for this income.")
    if cont:
        if cont >= 20: notes.append(f"{cont}yr contract — very secure.")
        elif cont >= 10: notes.append(f"{cont}yr contract — adequate.")
        else: risks.append(f"Only {cont}yr remaining — short term risk.")
    if pool and pool > 0:
        if pool >= 20: notes.append(f"{pool} pool units — good diversification.")
        elif pool >= 10: notes.append(f"{pool} pool units.")
        else: risks.append(f"Only {pool} pool units — small income base.")
    if price and income:
        roi = round(income / price * 100, 1)
        if roi >= 15: notes.append(f"{roi}% ROI — strong return.")
        elif roi >= 10: notes.append(f"{roi}% ROI.")
    if not notes and not risks: notes.append("Review financials before proceeding.")
    if not bc: action.append("Request BC salary breakdown.")
    if not pool: action.append("Verify pool unit schedule.")
    if not cont: action.append("Confirm contract term remaining.")
    result = {
        "id": src.replace('.','-') + '-' + str(abs(hash(name+url)) % 100000).zfill(5),
        "name": name.strip(),
        "region": reg,
        "price": price,
        "unit_price": unit_price,
        "price_source": price_source,
        "net_income": income,
        "multiplier": mult,
        "bc_percent": bc,
        "contract_years": cont,
        "pool_units": pool or 0,
        "weekly_rent_per_unit": None,
        "status": "active",
        "url": url,
        "source": src,
        "notes": " ".join(notes),
        "risks": " ".join(risks),
        "action": " ".join(action),
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "last_fetched": datetime.now().isoformat()
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

def extract_pool(t):
    m = re.search(r'Letting\s+Pool[:\s]+(\d+)', t, re.I)
    if m: return int(m.group(1))
    m = POOL_RE.search(t)
    return int(m.group(1)) if m else 0

def extract_contract(t):
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

def quality_score(p):
    score = 0
    price = p.get("price", 0) or 0
    ni = p.get("net_income", 0) or 0
    mult = p.get("multiplier", 0) or 0
    pool = p.get("pool_units", 0) or 0
    cont = p.get("contract_years") or 0
    bc = p.get("bc_percent") or 0
    name = (p.get("name") or "").lower()
    region = (p.get("region") or "").lower()
    loc = f"{name} {region}"
    if price > 0: score += 25
    if ni > 0: score += 25
    if mult and 3 <= mult <= 5: score += 20
    elif mult and 5 < mult <= 6.5: score += 10
    elif mult and mult > 8: score -= 15
    if bc and bc <= 70: score += 10
    elif bc and bc > 80: score -= 15
    if pool >= 20: score += 10
    elif pool >= 10: score += 5
    if cont and cont >= 20: score += 10
    elif cont and cont >= 10: score += 5
    if price and ni:
        roi = ni / price * 100
        if roi >= 15: score += 10
        elif roi >= 10: score += 5
    # FIX #16 — High net income bonus (大体量 listing 入榜奖励)
    if ni >= 500_000: score += 15
    elif ni >= 300_000: score += 8
    elif ni >= 150_000: score += 4

    # FIX #21 — South Brisbane / Eight Mile Plains corridor bonus
    if "eight mile plains" in loc:
        score += 12
    elif any(sub in loc for sub in EMP_RING_SUBURBS):
        score += 8

    return score

def is_good_candidate(p):
    name = p.get("name","").lower()
    price = p.get("price", 0) or 0
    ni = p.get("net_income", 0) or 0
    mult = p.get("multiplier", 0) or 0
    if price == 0 and ni == 0: return False
    if mult and mult > 15: return False
    if price and ni and price < ni: return False
    junk = ['caretaking only','sign up','more information','click here',
             'call 04','cooperative committee','add on permanent',
             'asking price','darwin','sale by expression','under contract'] + NON_QLD
    if any(j in name for j in junk): return False
    if is_non_qld(name): return False
    return True

# ── ResortBrokers ─────────────────────────────────────────────────────────────
def fetch_resortbrokers_detail(browser, href, name):
    page = new_page(browser)
    try:
        if not goto(page, href, timeout=30000, extra=2000): return 0, None, None, None
        t = norm(page.inner_text("body"))
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
                print(f"  [{i+1}] {title[:40]} — fetching detail...")
                time.sleep(random.uniform(0.5, 1.5))
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
                    time.sleep(random.uniform(0.5, 1.5))
                    dp = new_page(browser)
                    try:
                        if goto(dp, href, timeout=30000, extra=2000):
                            dt = norm(dp.inner_text("body"))
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

# ── TheOnsiteManager (FIX #10 — new Angular SPA, April 2026) ─────────────────
def fetch_onsite_detail(browser, href, income):
    page = new_page(browser)
    try:
        if not goto(page, href, timeout=30000, extra=2000): return 0, None, None, None, 0
        t = norm(page.inner_text("body"))
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
        # FIX #15 — "Total Purchase Price: $X,XXX,XXX" fallback (undisclosed multiplier listings)
        if not price:
            m = re.search(r'Total Purchase Price[:\s]+\$?\s*([\d,]+)', t, re.I)
            if m: price = parse_price('$' + m.group(1).replace(',',''))
        if not price:
            m = re.search(r'Purchase Price[:\s]+\$?\s*([\d,]+)', t, re.I)
            if m: price = parse_price('$' + m.group(1).replace(',',''))
        pool = extract_pool(t)
        cont = extract_contract(t)
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

def fetch_onsite(browser):
    # FIX #10 — new Angular SPA (April 2026 platform relaunch)
    # FIX #11 — title from .card-location suburb (not .card-title which is just type label)
    # FIX #11 — pagination: .pagination button:last-child:not([disabled])
    # FIX #11 — card unique id from .card-id for dedup stability
    src2, base = "theonsitemanager.com.au", "https://www.theonsitemanager.com.au"
    url = base + "/management-rights"
    out = []
    page = new_page(browser)
    try:
        if not goto(page, url): return out
        try:
            page.wait_for_selector("app-listing-card", timeout=20000)
        except Exception:
            print(f"  [{src2}] timeout waiting for app-listing-card")
            return out
        page.wait_for_timeout(2000)

        page_num = 1
        while True:
            cards = page.query_selector_all("app-listing-card")
            print(f"  [{src2}] page {page_num}: {len(cards)} cards")

            for i, card in enumerate(cards):
                try:
                    t = norm(card.inner_text())
                    if is_non_qld(t): continue

                    # link
                    link_el = card.query_selector("a.card[href]")
                    href = link_el.get_attribute("href") if link_el else None
                    if href and not href.startswith("http"): href = base + href

                    # FIX #11 — use suburb from .card-location as title, not .card-title (type label)
                    loc_el = card.query_selector(".card-location")
                    raw_loc = norm(loc_el.inner_text()) if loc_el else ""
                    # strip SVG pin artefact (leading non-alpha chars), then split on comma
                    raw_loc = re.sub(r'^[^a-zA-Z]+', '', raw_loc).strip()
                    suburb = (raw_loc.split(',')[0].strip() + ' QLD') if raw_loc else get_region(t)

                    # FIX #11 — card-id for stable unique name
                    id_el = card.query_selector(".card-id")
                    card_id_num = re.sub(r'[^0-9]', '', id_el.inner_text()) if id_el else ""
                    # FIX #12 — include card_id so dedup never false-positive on suburb
                    title = f"{suburb} #{card_id_num}" if card_id_num else suburb
                    if not title or len(title) < 4: title = f"QLD MR {card_id_num}"
                    if is_junk_title(title): continue

                    # region
                    region = get_region(suburb + " " + t)

                    # stats from .mr-row
                    income, remuneration, multiplier = 0, 0, 0.0
                    mr_rows = card.query_selector_all(".mr-row")
                    for row in mr_rows:
                        lbl_el = row.query_selector(".mr-label")
                        val_el = row.query_selector(".mr-val")
                        if not lbl_el or not val_el: continue
                        lbl = lbl_el.inner_text().strip().lower()
                        raw = val_el.inner_text().strip()
                        if "net income" in lbl:
                            income = parse_price(raw)
                        elif "remuneration" in lbl:
                            remuneration = parse_price(raw)
                        elif "multiplier" in lbl:
                            mm = re.search(r'([\d.]+)', raw)
                            if mm: multiplier = float(mm.group(1))

                    # manager's estate / included real estate price
                    unit_price = 0
                    for row in mr_rows:
                        lbl_el = row.query_selector(".mr-label")
                        val_el = row.query_selector(".mr-val")
                        if lbl_el and val_el:
                            lbl = lbl_el.inner_text().strip().lower()
                            if "estate" in lbl or "included real estate" in lbl or ("manager" in lbl and ("unit" in lbl or "estate" in lbl)):
                                v = parse_price(val_el.inner_text())
                                if v > 100000:
                                    unit_price = v

                    # FIX #22 — unified onsite pricing model
                    total_p, biz_p, unit_p, is_mr_unit = extract_total_price(t)
                    headline_price = extract_card_headline_price(card)
                    business_price = int(income * multiplier) if income > 0 and multiplier > 0 else 0
                    if unit_price == 0 and is_mr_unit and unit_p > 100000:
                        unit_price = unit_p

                    price = 0
                    price_source = None
                    if headline_price > 100000:
                        price = headline_price
                        price_source = "card_headline"
                    elif business_price > 100000 and unit_price > 100000:
                        price = business_price + unit_price
                        price_source = "business_plus_unit"
                    elif total_p > 100000:
                        price = total_p
                        price_source = "card_total_regex"
                    elif business_price > 100000:
                        price = business_price
                        price_source = "multiplier_fallback"

                    pool = extract_pool(t)
                    cont = extract_contract(t)
                    bc = extract_bc_percent(t, income) if income else None
                    if bc is None and remuneration > 0 and income > 0:
                        bc = round(remuneration / income * 100, 1)

                    headline_gap = abs((headline_price or 0) - (business_price or 0)) if headline_price and business_price else 0
                    needs_detail = bool(href and (
                        multiplier == 0 or
                        income >= 400_000 or
                        unit_price > 100000 or
                        headline_price > 100000 or
                        total_p > 100000 or
                        headline_gap >= 100000
                    ))
                    if needs_detail:
                        time.sleep(random.uniform(0.3, 0.8))
                        det_p, det_bc, det_pool, det_cont, det_unit = fetch_onsite_detail(browser, href, income)
                        if det_unit > 0:
                            unit_price = det_unit
                        if det_p > 100000:
                            price = det_p
                            price_source = "detail_total"
                        elif headline_price > 100000:
                            price = headline_price
                            price_source = "card_headline"
                        elif business_price > 100000 and unit_price > 100000:
                            price = business_price + unit_price
                            price_source = "business_plus_unit"
                        elif total_p > 100000:
                            price = total_p
                            price_source = "card_total_regex"
                        elif business_price > 100000:
                            price = business_price
                            price_source = "multiplier_fallback"
                        if det_bc is not None:
                            bc = det_bc
                        if det_pool:
                            pool = det_pool
                        if det_cont:
                            cont = det_cont

                    # FIX #15 — calc multiplier from price/income when site shows "undisclosed"
                    if price > 100000 and income > 0 and multiplier == 0:
                        multiplier = round(price / income, 2)
                    if price > 100000 and title:
                        out.append(make_listing(title, price, income, region, href, src2,
                                                bc, pool, cont, unit_price=unit_price, price_source=price_source))
                except Exception as e:
                    print(f"  card {i} error: {e}")

            # FIX #11 — pagination: last button in .pagination, check not disabled
            next_btn = page.query_selector(".pagination button:last-child")
            if not next_btn or next_btn.get_attribute("disabled") is not None:
                break
            # verify it says "Next" (safety check)
            btn_txt = next_btn.inner_text()
            if "next" not in btn_txt.lower():
                break
            next_btn.click()
            page_num += 1
            page.wait_for_timeout(4000)
            try:
                page.wait_for_selector("app-listing-card", timeout=15000)
            except Exception:
                break

    except Exception as e:
        print(f"  {src2} fatal: {e}")
    finally:
        page.context.close()

    print(f"  [{src2}] total scraped: {len(out)}")
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
            for line in block.split(" "):
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

# FIX #4/#14 — dedup by URL + name + (price,income,region) fingerprint
def dedup(items):
    seen_urls, seen_names, seen_fingerprints, out, n = set(), {}, set(), [], 0
    for item in items:
        url_key = item.get("url","").split("?")[0].lower().strip("/")
        name_key = re.sub(r'\s+',' ', item["name"].lower().strip())[:50]
        # FIX #14 — catch same-property listings by different brokers
        price = item.get("price", 0) or 0
        income = item.get("net_income", 0) or 0
        region = (item.get("region") or "").lower().strip()
        # Only use fingerprint if both price AND income are non-zero (avoid false matches on 0,0)
        fp = (price, income, region) if price > 0 and income > 0 else None

        if url_key and url_key in seen_urls:
            n += 1; continue
        if name_key in seen_names:
            n += 1; continue
        if fp and fp in seen_fingerprints:
            n += 1; continue

        if url_key: seen_urls.add(url_key)
        seen_names[name_key] = True
        if fp: seen_fingerprints.add(fp)
        out.append(item)
    return out, n

def apply_quality_filter(items, target=80):
    # FIX #16: high-income listings always included regardless of multiplier penalty or top-N cutoff
    HIGH_INCOME_THRESHOLD = 500_000
    good = [p for p in items if is_good_candidate(p)]
    removed_hard = len(items) - len(good)
    scored = sorted(good, key=quality_score, reverse=True)
    # FIX #20: stamp quality_score into each listing dict
    for p in scored:
        p["quality_score"] = quality_score(p)

    # Separate high-income must-keep listings
    high_income = [p for p in scored
                   if (p.get("net_income") or 0) >= HIGH_INCOME_THRESHOLD
                   and p.get("price", 0) > 0]
    normal = [p for p in scored if p not in high_income]

    full_data = [p for p in normal if p.get("price",0) > 0 and p.get("net_income",0) > 0]
    partial = [p for p in normal if p not in full_data]

    # High-income listings always included; fill remaining slots from normal
    final = list(high_income)
    remaining = max(target - len(final), 0)
    final += full_data[:remaining]
    remaining2 = target - len(final)
    if remaining2 > 0:
        final += partial[:remaining2]

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
    print("PMR Data Fetcher (Playwright) v29 Starting...")
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S\n"))
    fetchers = [
        ("accomproperties.com.au",        fetch_accom),
        ("resortbrokers.com.au",           fetch_resortbrokers),
        ("theonsitemanager.com.au",        fetch_onsite),
        ("siremanagementrights.com.au",    fetch_sire),
        ("businessforsale.com.au",         fetch_bfs),
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
    final, hard_removed, soft_removed = apply_quality_filter(unique, target=100)
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

    tv = sum(l["price"] for l in final)
    ti = sum(l["net_income"] for l in final)
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
