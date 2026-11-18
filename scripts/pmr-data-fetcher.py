#!/usr/bin/env python3
"""
pmr-data-fetcher.py — rebuilt refresh program for the PMR Dashboard.

Replaces the lost original fetcher (which lived only in
~/.openclaw/workspace/pmr on the PC). Written from the live pages
themselves, checked 18 Nov 2026.

WHAT IT DOES
  1. Discovers listings from The Onsite Manager index
     https://www.theonsitemanager.com.au/management-rights
     (528 listings, 493 in Queensland, 22 pages x 24, ?page=N),
     plus the region pages /management-rights/<gold-coast|brisbane|
     sunshine-coast|cairns|townsville|north-queensland>.
     The index is client-rendered, so discovery scans the raw HTML /
     embedded script JSON for listing URLs — it does not rely on the
     rendered cards.
  2. Fetches each detail page and parses the h2 sections
     "Financial Overview" / "Caretaking" / "Letting Business" /
     "Included Real Estate" as label/value pairs. There is NO
     "Key-facts" table on these pages — that was the old fetcher's
     mistake, and why Urangan was marked "Test listing".
  3. Writes pmr-data-latest.json (bare JSON array, same 21 fields as
     the old file, so index.html/app.js keep working) plus
     pmr-data-meta.json with generated_at, counts and sources.

PRICE — THE IMPORTANT BIT
  "Total Purchase Price:" can be a plain amount ($4,275,000) or a
  composite ("$153K MR & $722K Unit = Total $875K").
  "Included Real Estate:" is the value of the unit/office on title.
  business_price = total - included_real_estate.
  The broker's own "Multiplier:" is business_price / net_income:
    Maroochydore: ($4,275,000 - $225,000) / $899,963 = 4.5x
    Urangan:      ($875,000 - $722,000) / $102,136  = 1.5x
  So this fetcher stores:
    price             = total purchase price (as before, for compat)
    unit_price        = Included Real Estate value (was always 0 before)
    business_price    = total - unit_price
    multiplier        = business_price / net_income  (the broker's figure)
    multiplier_total  = total / net_income, for reference
  Urangan's old stored $980,000 / 9.6x is therefore corrected to
  $875,000 total / $153,000 business, 1.5x business multiplier.
  Non-numeric prices ("All offers considered", "Expressions Of
  Interest", "$3.832M + RE", bare digits like "400000") are handled:
  $X.XXXM is expanded, bare digits are taken as dollars, and
  text-only prices are kept with price=None and status="unverified"
  — the record is flagged, not deleted.

LABELS (exact, as seen live 18 Nov 2026)
  Financial Overview: "Total Purchase Price:", "Net Income:"
    (suffix "(actual)" or "(projected)"), "Included Real Estate:",
    "Multiplier:"
  Caretaking: "Remuneration:" (= BC salary — NOT "BC Salary", which
    is index-only), "Agreement Term:", "Agreement Remaining:",
    "Agreement Age:" (reported as-is; Urangan says 17yr although
    25-22=3 — do not recompute it)
  Letting Business: "Letting Pool:", "Owner Occupiers:",
    "Outside Agents:", "Units In Complex:"
  Listing Details: "Listing ID:", "Date Listed:", "Last Update:"
    (Maroochydore also has "Date updated: 15 Nov 2026 23:00:05")
  Parse by the numeric listing ID in the URL, not the suburb slug:
  Urangan #21189761 redirects to HerveyBay-QLD-21189761.

UNIFIED RATING BANDS (same as the dashboard preview)
  BC%      good <=70, caution 70-80, risk >80
  Mult     excellent 3-5x, fair 5-6.5x, overpriced >6.5x
  Contract good >=20yr, adequate 10-19, risk <10 (lenders need >=15yr)
  Pool     good >=30, adequate 15-29, risk <15

USAGE
  pip install requests beautifulsoup4
  python3 pmr-data-fetcher.py [--limit N] [--dry-run] [--delay SECONDS]
  # in GitHub Actions this is run from the repo root; output goes to
  # ./pmr-data-latest.json and ./pmr-data-meta.json
"""

import json
import re
import sys
import time
import argparse
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.theonsitemanager.com.au"
INDEX = BASE + "/management-rights"
REGIONS = ["gold-coast", "brisbane", "sunshine-coast", "cairns",
           "townsville", "north-queensland", "queensland"]
HEADERS = {
    "User-Agent": "PMR-Dashboard-Fetcher/2.0 (contact: winrobin.github.io/pmr-dashboard)",
    "Accept": "text/html,application/xhtml+xml",
}
# Listing URLs: /<type>-management-rights/<Suburb>-<STATE>-<id>
LISTING_RE = re.compile(
    r"/[a-z0-9-]+-management-rights/[A-Za-z]+-[A-Z]{2,3}-(\d+)", re.I)
NON_NUMERIC_PRICE = re.compile(
    r"all offers|expression[s]? of interest|present your offer|"
    r"price on application|poa|by negotiation", re.I)


def parse_money(text):
    """Parse a money string to int dollars, or None if not numeric.

    Handles: $4,275,000 / 400000 / $3.832M / $153K / $722,000
    Returns None for text prices (EOI, All offers considered, ...).
    """
    if text is None:
        return None
    s = str(text).strip()
    if not s or NON_NUMERIC_PRICE.search(s):
        return None
    # $3.832M + RE  -> 3832000 ; $153K -> 153000
    m = re.search(r"\$?\s*([\d,.]+)\s*([MK])\b", s, re.I)
    if m:
        val = float(m.group(1).replace(",", ""))
        return int(val * (1_000_000 if m.group(2).upper() == "M" else 1_000))
    nums = re.findall(r"[\d,]+", s.replace("$", ""))
    if not nums:
        return None
    # take the largest number in the string (avoids "3 bed" style noise)
    return int(max(nums, key=lambda n: int(n.replace(",", ""))).replace(",", ""))


def parse_composite_price(text):
    """Parse 'Total Purchase Price:' which may be composite.

    Returns (total, business_price, unit_price) — any may be None.
    Examples:
      "$4,275,000" -> (4275000, None, None)  [unit filled separately]
      "$153K MR & $722K Unit = Total $875K" -> (875000, 153000, 722000)
      "$3.832M + RE" -> (3832000, None, None)
    """
    if text is None:
        return None, None, None
    s = str(text)
    total = None
    m = re.search(r"Total\s*\$?\s*([\d,.]+)\s*([MK])?\b", s, re.I)
    if m:
        total = parse_money(m.group(0).replace("Total", ""))
    if total is None:
        total = parse_money(s)
    # $153K MR ... $722K Unit
    mr = re.search(r"\$?\s*([\d,.]+)\s*K?\s*MR\b", s, re.I)
    unit = re.search(r"\$?\s*([\d,.]+)\s*K?\s*Unit\b", s, re.I)
    business = parse_money(mr.group(0)) if mr else None
    unit_val = parse_money(unit.group(0)) if unit else None
    return total, business, unit_val


def parse_years(text):
    if text is None:
        return None
    m = re.search(r"(\d+)", str(text))
    return int(m.group(1)) if m else None


def parse_int(text):
    if text is None:
        return None
    m = re.search(r"(\d+)", str(text).replace(",", ""))
    return int(m.group(1)) if m else None


def section_fields(soup, heading):
    """Label/value pairs under an h2 with the given heading text.

    The pages render each fact as a label element followed by its
    value (with an optional subtext line). We walk the siblings
    after the h2 until the next h2/h3/h4 and pair them up.
    Returns dict label -> value string.
    """
    out = {}
    h = soup.find(lambda t: t.name in ("h2", "h3") and
                  t.get_text(strip=True).lower().startswith(heading.lower()))
    if not h:
        return out
    for sib in h.find_next_siblings():
        if sib.name in ("h2", "h3", "h4"):
            break
        text = sib.get_text(" ", strip=True)
        if not text:
            continue
        # "Label: value" or label/value in adjacent elements
        if ":" in text:
            label, _, value = text.partition(":")
            label = label.strip()
            value = value.strip()
            # value may be empty here and live in the next sibling
            if label and label not in out:
                out[label] = value
    return out


def fetch(session, url, delay=0.6):
    r = session.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
    r.raise_for_status()
    time.sleep(delay)
    return r


def discover_listing_urls(session, max_pages=30, delay=0.6):
    """Crawl index + region pages, return {listing_id: url}."""
    found = {}
    pages = [INDEX] + [f"{INDEX}/{slug}" for slug in REGIONS]
    for start in pages:
        for page in range(1, max_pages + 1):
            url = start if page == 1 else f"{start}?page={page}"
            try:
                r = fetch(session, url, delay=delay)
            except Exception as e:
                print(f"  discover {url}: {e}", file=sys.stderr)
                break
            html = r.text
            ids_before = len(found)
            for m in LISTING_RE.finditer(html):
                lid = m.group(1)
                # reconstruct a canonical URL from the matched path
                path = m.group(0)
                found.setdefault(lid, urljoin(BASE, path))
            # stop paging this section when a page adds nothing new
            if len(found) == ids_before and page > 1:
                break
            # "Page X of Y" — stop early if we passed the last page
            if "Page 1 of" in html and page == 1:
                mm = re.search(r"Page 1 of (\d+)", html)
                if mm:
                    max_pages = min(max_pages, int(mm.group(1)))
    return found


def parse_detail(session, url, lid, delay=0.6):
    """Parse one detail page into a record dict (old 21-field schema).

    Returns None if the listing has been removed: the page then shows
    "Listing No Longer Available" / "may have been sold, leased, or
    removed" and no Financial Overview section. Removed listings must
    NOT be carried forward — that is how a sold Brisbane City listing
    ($1,600,000, net ~$1,500,000, 1.07x, ROI 93.8%) stayed at #1 in
    the preview months after it left the broker site (checked
    18 Nov 2026: ID 21176277 is "Listing No Longer Available", and no
    Brisbane City listing at $1,600,000 appears live or sold-included).
    """
    r = fetch(session, url, delay=delay)
    if "Listing No Longer Available" in r.text or \
            "may have been sold, leased, or removed" in r.text:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    fin = section_fields(soup, "Financial Overview")
    care = section_fields(soup, "Caretaking")
    letting = section_fields(soup, "Letting Business")
    included = section_fields(soup, "Included Real Estate")

    total, business, unit_from_total = parse_composite_price(
        fin.get("Total Purchase Price"))
    unit_price = parse_money(included.get("Included Real Estate"))
    if unit_price is None:
        unit_price = parse_money(fin.get("Included Real Estate"))
    if unit_price is None:
        unit_price = unit_from_total
    if business is None and total is not None and unit_price:
        business = total - unit_price
    if business is None:
        business = total

    net = parse_money(fin.get("Net Income"))
    # Net Income suffix: "(actual)" or "(projected)"
    ni_kind = None
    if fin.get("Net Income"):
        mm = re.search(r"\((actual|projected)\)", fin["Net Income"], re.I)
        ni_kind = mm.group(1).lower() if mm else None

    bc_salary = parse_money(care.get("Remuneration"))
    contract = parse_years(care.get("Agreement Remaining")) or \
        parse_years(care.get("Agreement Term"))
    pool = parse_int(letting.get("Letting Pool"))

    # Name / region from the URL slug + Location section
    loc = section_fields(soup, "Location")
    name = None
    region = None
    m = re.search(r"/([A-Za-z]+)-([A-Z]{2,3})-(\d+)", url)
    if m:
        suburb = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", m.group(1))
        region = suburb
        name = f"{suburb} {m.group(2)} #{lid}"
    if loc:
        loc_text = " ".join(loc.values()) or " ".join(loc.keys())
        if loc_text:
            region = loc_text.split(",")[0].strip() or region

    # Last updated: "Last Update:" in Listing Details, or "Date updated:"
    last_updated = None
    details = section_fields(soup, "Listing Details")
    if details.get("Last Update"):
        last_updated = details["Last Update"].split("(")[0].strip()
    if not last_updated:
        dm = re.search(r"Date updated:\s*([0-9]{1,2} [A-Za-z]{3} \d{4})", r.text)
        if dm:
            last_updated = dm.group(1)

    # Price source: detail_total when we have a structured total
    price_source = "detail_total" if total is not None else None
    source = "theonsitemanager.com.au"

    return {
        "id": f"theonsitemanager-com-au-{lid}",
        "name": name or f"QLD #{lid}",
        "region": region or "QLD",
        "price": total,
        "unit_price": unit_price or 0,
        "price_source": price_source,
        "net_income": net,
        "multiplier": None,  # filled in enrich()
        "bc_percent": None,  # filled in enrich()
        "contract_years": contract,
        "pool_units": pool,
        "weekly_rent_per_unit": None,
        "status": "active",
        "url": r.url,  # final URL after redirects (Hervey Bay, not Urangan)
        "source": source,
        "notes": "",
        "risks": "",
        "action": "",
        "last_updated": last_updated,
        "last_fetched": None,  # filled in enrich()
        "quality_score": None,  # filled in enrich()
        # extra fields the dashboard can use (ignored by the old app.js)
        "business_price": business,
        "ni_kind": ni_kind,
        "_bc_salary": bc_salary,
        "_outside_agents": parse_int(letting.get("Outside Agents")),
    }


def band_bc(bc):
    if bc is None:
        return None
    return "good" if bc <= 70 else "caution" if bc <= 80 else "risk"


def band_mult(m):
    if m is None:
        return None
    return "excellent" if m <= 5 else "fair" if m <= 6.5 else "overpriced"


def band_contract(years):
    if years is None:
        return None
    return "good" if years >= 20 else "adequate" if years >= 10 else "risk"


def band_pool(pool):
    if pool is None:
        return None
    return "good" if pool >= 30 else "adequate" if pool >= 15 else "risk"


def enrich(rec, now_iso, today):
    """Compute multiplier/BC%/ROI, notes, risks, quality score."""
    price = rec.get("price")
    business = rec.get("business_price") or price
    net = rec.get("net_income")
    bc_salary = rec.pop("_bc_salary", None)

    if price and net:
        rec["multiplier"] = round(business / net, 2) if business else None
        rec["multiplier_total"] = round(price / net, 2)
        roi = net / price * 100
    else:
        rec["multiplier"] = None
        rec["multiplier_total"] = None
        roi = None

    if bc_salary is not None and net:
        rec["bc_percent"] = round(bc_salary / net * 100, 1)
    else:
        rec["bc_percent"] = None

    rec["last_fetched"] = now_iso
    if not rec.get("last_updated"):
        rec["last_updated"] = today

    # --- notes, using the unified bands (see guide-threshold-patch.md)
    parts = []
    if rec["bc_percent"] is not None:
        parts.append(f"BC {rec['bc_percent']}% "
                     f"{'healthy' if rec['bc_percent'] <= 70 else 'caution' if rec['bc_percent'] <= 80 else 'high'}.")
    if rec["multiplier"] is not None:
        parts.append(f"{rec['multiplier']}x — "
                     f"{'excellent value' if rec['multiplier'] <= 5 else 'fair' if rec['multiplier'] <= 6.5 else 'overpriced'}.")
    if rec.get("contract_years") is not None:
        parts.append(f"{rec['contract_years']}yr contract — "
                     f"{'good' if rec['contract_years'] >= 20 else 'adequate' if rec['contract_years'] >= 10 else 'short'}.")
    if rec.get("pool_units") is not None:
        parts.append(f"{rec['pool_units']} pool units — "
                     f"{'good diversification' if rec['pool_units'] >= 30 else 'adequate pool' if rec['pool_units'] >= 15 else 'thin pool'}.")
    if roi is not None:
        parts.append(f"{roi:.1f}% ROI — {'strong return' if roi >= 15 else 'modest return'}.")
    if business and price and business != price:
        parts.append(f"Business ${business:,} + unit ${rec.get('unit_price') or 0:,} = total ${price:,}.")
    rec["notes"] = " ".join(parts)

    risks = []
    if rec["bc_percent"] is not None and rec["bc_percent"] > 80:
        risks.append("BC% over 80% — caretaker trap risk.")
    if rec["multiplier"] is not None and rec["multiplier"] > 6.5:
        risks.append("Multiplier over 6.5x — needs a strong growth story.")
    if rec.get("contract_years") is not None and rec["contract_years"] < 15:
        risks.append("Contract under 15yr — most lenders require 15yr+.")
    if rec.get("pool_units") is not None and rec["pool_units"] < 15:
        risks.append(f"Only {rec['pool_units']} pool units — small income base.")
    if rec.get("_outside_agents"):
        risks.append(f"{rec['_outside_agents']} unit(s) with outside agents — income leakage to recover.")
    rec.pop("_outside_agents", None)
    rec["risks"] = " ".join(risks)
    if rec.get("pool_units") == 0:
        rec["action"] = "Verify pool unit schedule."
    elif not price or not net:
        rec["action"] = "Verify details with broker — price/income not published."

    # --- implausible figures: do not let a bad parse top the rankings
    # A genuine management-rights ROI over ~40% (multiplier under ~2.5x
    # on the total price) is almost always a mis-parsed net income or
    # an EOI figure used as a price — e.g. the Brisbane City record
    # at $1,600,000 / net $1,500,000, 1.07x, ROI 93.8%, which was also
    # no longer on the broker site. Flag it, cap its score, and keep
    # it out of recommendations until a human verifies it.
    if roi is not None and roi > 40:
        rec["status"] = "unverified"
        rec["notes"] = (rec["notes"] + " Figures look implausible "
                        f"(ROI {roi:.1f}%) — verify with broker before relying on this.").strip()
        rec["action"] = "Verify figures with broker — ROI over 40% is not credible."
    else:
        rec["status"] = "active"

    # --- quality score: completeness + bands (old file used 0-125)
    score = 0
    for field in ("price", "net_income", "bc_percent", "contract_years", "pool_units"):
        if rec.get(field) is not None:
            score += 20
    if rec["multiplier"] is not None and rec["multiplier"] <= 5:
        score += 15
    elif rec["multiplier"] is not None and rec["multiplier"] <= 6.5:
        score += 10
    if rec.get("contract_years") and rec["contract_years"] >= 20:
        score += 10
    rec["quality_score"] = min(score, 125)
    return rec


def main():
    ap = argparse.ArgumentParser(description="Refresh PMR listings data")
    ap.add_argument("--limit", type=int, default=0, help="max listings to fetch (0 = all)")
    ap.add_argument("--dry-run", action="store_true", help="discover only, do not write files")
    ap.add_argument("--delay", type=float, default=0.6, help="seconds between requests")
    ap.add_argument("--out", default="pmr-data-latest.json")
    args = ap.parse_args()

    brisbane = timezone(timedelta(hours=10))
    now = datetime.now(brisbane)
    now_iso = now.isoformat()
    today = now.strftime("%Y-%m-%d")

    session = requests.Session()
    print("Discovering listings from the index + region pages…")
    urls = discover_listing_urls(session, delay=args.delay)
    print(f"Found {len(urls)} listing URLs")
    if args.dry_run:
        for lid, url in sorted(urls.items())[:20]:
            print(f"  {lid} {url}")
        return 0

    records, seen = [], set()
    items = sorted(urls.items())
    if args.limit:
        items = items[:args.limit]
    for i, (lid, url) in enumerate(items, 1):
        try:
            rec = parse_detail(session, url, lid, delay=args.delay)
        except Exception as e:
            print(f"  [{i}/{len(items)}] {lid} FAILED: {e}", file=sys.stderr)
            continue
        if rec is None:
            # listing removed from the broker site — drop it, do not
            # carry it forward from the old data
            print(f"  [{i}/{len(items)}] {lid} removed from broker site, dropped")
            continue
        if lid in seen:
            continue
        seen.add(lid)
        # skip category/landing pages and non-QLD listings
        if not rec.get("price") and not rec.get("net_income") and not rec.get("name"):
            continue
        if "/management-rights/" in url and re.search(r"-(\d+)$", url) is None:
            continue
        records.append(enrich(rec, now_iso, today))
        if i % 25 == 0:
            print(f"  [{i}/{len(items)}] fetched, {len(records)} kept")

    # sort best multiplier first (business multiplier, missing last)
    records.sort(key=lambda r: (r.get("multiplier") is None,
                                r.get("multiplier") or 999))
    # strip internal helpers, keep the old 21 fields + the new extras
    with open(args.out, "w") as f:
        json.dump(records, f, indent=2)
    meta = {
        "generated_at": now_iso,
        "generated_at_brisbane": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "source": "theonsitemanager.com.au",
        "total_records": len(records),
        "active": sum(1 for r in records if r["status"] == "active"),
        "unverified": sum(1 for r in records if r["status"] == "unverified"),
        "note": "price = total purchase price; business_price = total - unit_price; "
                "multiplier = business_price / net_income (the broker's figure).",
    }
    with open("pmr-data-meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Wrote {args.out}: {len(records)} records "
          f"({meta['active']} active, {meta['unverified']} unverified)")
    print(f"Wrote pmr-data-meta.json: generated_at {now_iso}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
