#!/usr/bin/env python3
"""
pmr-data-fetcher.py — rebuilt refresh program for the PMR Dashboard.
Version 3 — API-first (18 Nov 2026).

WHAT IT DOES
  1. Fetches listings from the broker's own public JSON API, named
     in the site's robots.txt — no API key or sign-in needed:
       GET https://www.theonsitemanager.com.au/api/v1/listings.php
           ?class=Management%20Rights&page=N&limit=100
     Response: {"success":true, "data":[...],
                "pagination":{"total":528,"page":1,"limit":100,"pages":6}}
     Loop page=1..pages. limit=100 is the largest usable page size
     (above 100 it falls back to 20). This replaces v2's HTML crawl,
     which only ever saw the first page of the client-rendered index
     (?page=N returns the same first-page HTML) and found just 98
     listings on its first live run, out of ~528.
  2. Keeps only Queensland listings (state == "QLD", ~493 of 528).
     Removed listings simply stop appearing in the API, so they
     drop out automatically — no "Listing No Longer Available"
     page to detect.
  3. Maps API fields to the dashboard's 21-field schema and writes
     pmr-data-latest.json (bare JSON array) plus pmr-data-meta.json
     with generated_at, counts and sources.

API FIELDS (verified live 18 Nov 2026)
  pageId (stable ID), suburb, state, postcode, region (hub slug),
  price (numeric total, e.g. 400000), priceView (display string,
  e.g. "$3.832M + RE", "All offers considered"),
  takings (net income), takingsBasis ("actual"/"projected"),
  mr_remuneration (BC salary), mr_unitsLettingPool (pool),
  mr_unitValue (included real estate / unit value),
  mr_unitsTotal (units in complex), mr_agreementRemaining
  (contract years remaining), timestamp (last updated),
  category, status, title, description, listingAgentName.
  Listing URL (new format, verified live 20 Nov 2026): the broker
  rebuilt its site and old /management-rights/{pageId}/{slug}
  URLs now redirect to the broker homepage, which broke every
  View link on the dashboard. Detail pages now live at
    /{category-slug}/{Suburb}-{STATE}-{pageId}
  e.g. /permanent-management-rights/CARRARA-QLD-21205549 and
  /resort--holiday-management-rights/AirlieBeach-QLD-21205437.
  The API returns no url field, so the fetcher builds it from
  category + suburb + state + pageId. Category mapping (each
  verified against a live detail page):
    Permanent -> permanent-management-rights
    Resort / Holiday, Holiday, Resort -> resort--holiday-management-rights
      (the site groups all three under "Resort and holiday")
    Caretaking -> caretaking-management-rights
    Corporate -> corporate-management-rights
    Retirement -> retirement-management-rights
    Off The Plan -> off-the-plan-management-rights (no QLD record
      uses it — all 19 are SHARJAH — so this is a fallback only)
  Robustness, verified live: the broker routes by pageId — a
  wrong category segment still lands on the right listing, and
  the suburb slug is case-insensitive (carrara-qld works as well
  as CARRARA-QLD). The suburb slug is the API suburb with
  whitespace removed, case preserved.

PRICE — THE IMPORTANT BIT
  business_price = price - mr_unitValue.
  The broker's own "Multiplier:" is business_price / net_income:
    Maroochydore: ($4,275,000 - $225,000) / $899,963 = 4.5x
    Urangan:      ($875,000 - $722,000) / $102,136  = 1.5x
  Stored: price = total, unit_price = mr_unitValue,
  business_price, multiplier = business_price / net_income,
  multiplier_total = total / net_income.
  Non-numeric priceView ("All offers considered", "Expressions Of
  Interest", "$3.832M + RE") is parsed the same way as v2; a
  record with no usable price or net income is kept with
  status="unverified", never deleted, and never allowed to top
  the recommendations (see enrich()).

UNIFIED RATING BANDS (same as the dashboard)
  BC%      good <=70, caution 70-80, risk >80
  Mult     excellent 3-5x, fair 5-6.5x, overpriced >6.5x
  Contract good >=20yr, adequate 10-19, risk <10 (lenders need >=15yr)
  Pool     good >=30, adequate 15-29, risk <15

NEW BADGE (22 Nov 2026)
  A listing shows NEW for 3 days after it first appears in our data.
  The fetcher stores first_seen (YYYY-MM-DD) per listing, carried
  forward from the previous pmr-data-latest.json, plus is_new
  (first_seen within the last 3 days). The old frontend badge used
  last_fetched, which the fetcher refreshes for every listing on
  every run, so it showed NEW on everything. Bootstrap: on the
  first run with this change, first_seen falls back to the broker's
  timestamp date so existing listings are not all tagged NEW.

USAGE
  pip install requests
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

import requests

API = "https://www.theonsitemanager.com.au/api/v1/listings.php"
HEADERS = {
    "User-Agent": "PMR-Dashboard-Fetcher/3.0 (contact: winrobin.github.io/pmr-dashboard)",
    "Accept": "application/json",
}
NON_NUMERIC_PRICE = re.compile(
    r"all offers|expression[s]? of interest|present your offer|"
    r"price on application|poa|by negotiation", re.I)


def parse_money(text):
    """Parse a money string to int dollars, or None if not numeric."""
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return int(text) if text else None
    s = str(text).strip()
    if not s or NON_NUMERIC_PRICE.search(s):
        return None
    m = re.search(r"\$?\s*([\d,.]+)\s*([MK])\b", s, re.I)
    if m:
        val = float(m.group(1).replace(",", ""))
        return int(val * (1_000_000 if m.group(2).upper() == "M" else 1_000))
    nums = re.findall(r"[\d,]+", s.replace("$", ""))
    if not nums:
        return None
    return int(max(nums, key=lambda n: int(n.replace(",", ""))).replace(",", ""))


def parse_composite_price(text):
    """Parse a composite total like '$153K MR & $722K Unit = Total $875K'.
    Returns (total, business_price, unit_price) — any may be None."""
    if text is None:
        return None, None, None
    s = str(text)
    total = None
    m = re.search(r"Total\s*\$?\s*([\d,.]+)\s*([MK])?\b", s, re.I)
    if m:
        total = parse_money(m.group(0).replace("Total", ""))
    if total is None:
        total = parse_money(s)
    mr = re.search(r"\$?\s*([\d,.]+)\s*K?\s*MR\b", s, re.I)
    unit = re.search(r"\$?\s*([\d,.]+)\s*K?\s*Unit\b", s, re.I)
    business = parse_money(mr.group(0)) if mr else None
    unit_val = parse_money(unit.group(0)) if unit else None
    return total, business, unit_val


def parse_int(text):
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return int(text)
    m = re.search(r"(\d+)", str(text).replace(",", ""))
    return int(m.group(1)) if m else None


def parse_date(text):
    """Parse a broker timestamp to a YYYY-MM-DD date string, or None.

    The API timestamp is ISO ("2026-11-21T13:57:10+10:00") or
    "15 Nov 2026 23:00:05". Used only to bootstrap first_seen on
    the first run with NEW tracking, so the first run does not tag
    all ~490 existing listings as NEW.
    """
    if not text:
        return None
    s = str(text).strip()
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except ValueError:
        pass
    for fmt in ("%d %b %Y %H:%M:%S", "%d %b %Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def fetch_api_page(session, page, limit=100, delay=0.3):
    """One page of the listings API. Returns (records, pagination)."""
    r = session.get(API, params={"class": "Management Rights",
                                 "page": page, "limit": limit},
                    headers=HEADERS, timeout=30)
    r.raise_for_status()
    time.sleep(delay)
    payload = r.json()
    if not payload.get("success", True):
        raise ValueError(f"API error on page {page}: {payload}")
    return payload.get("data", []), payload.get("pagination", {})


def discover_records(session, delay=0.3):
    """Fetch every page of the API. Returns all raw records."""
    all_records, page = [], 1
    while True:
        data, pagination = fetch_api_page(session, page, delay=delay)
        all_records.extend(data)
        pages = pagination.get("pages") or 1
        total = pagination.get("total")
        print(f"  API page {page}/{pages}: {len(data)} records "
              f"(total {total})")
        if page >= pages or not data:
            break
        page += 1
    return all_records


# Broker detail-page URL segments, verified live 20 Nov 2026
# (see module docstring). The site groups Resort / Holiday,
# Holiday and Resort under one "Resort and holiday" type.
CATEGORY_SLUGS = {
    "Permanent": "permanent-management-rights",
    "Resort / Holiday": "resort--holiday-management-rights",
    "Holiday": "resort--holiday-management-rights",
    "Resort": "resort--holiday-management-rights",
    "Caretaking": "caretaking-management-rights",
    "Corporate": "corporate-management-rights",
    "Retirement": "retirement-management-rights",
    "Off The Plan": "off-the-plan-management-rights",
}


def build_listing_url(api, lid):
    """Build the broker's new-format detail URL for one API record.

    https://www.theonsitemanager.com.au/{category-slug}/
        {Suburb}-{STATE}-{pageId}
    The API returns no url field. The broker routes by pageId, so
    the suburb slug (API suburb, whitespace removed, case kept)
    is cosmetic, but the /{segment}/{slug}-{state}-{id} shape is
    required — the old /management-rights/{id}/{slug} shape
    redirects to the broker homepage.
    """
    segment = CATEGORY_SLUGS.get((api.get("category") or "").strip(),
                                 "permanent-management-rights")
    suburb = re.sub(r"\s+", "", (api.get("suburb") or "QLD").strip())
    state = (api.get("state") or "QLD").strip().upper()
    return (f"https://www.theonsitemanager.com.au/{segment}/"
            f"{suburb}-{state}-{lid}")


def map_record(api):
    """Map one API record to the dashboard's 21-field schema."""
    lid = str(api.get("pageId") or api.get("id"))
    suburb = (api.get("suburb") or "").strip()
    state = (api.get("state") or "QLD").strip()
    price = parse_int(api.get("price"))
    price_view = api.get("priceView") or ""
    unit_price = parse_int(api.get("mr_unitValue")) or 0
    if price is None:
        # priceView may be composite ("$153K MR & $722K Unit = Total $875K")
        # or an abbreviated million ("$3.832M + RE")
        total, business, unit_from_view = parse_composite_price(price_view)
        price = total
        if unit_price == 0 and unit_from_view:
            unit_price = unit_from_view
    business = None
    if price is not None and unit_price:
        business = price - unit_price
    if business is None:
        business = price
    net = parse_int(api.get("takings"))
    bc_salary = parse_int(api.get("mr_remuneration"))
    contract = parse_int(api.get("mr_agreementRemaining"))
    pool = parse_int(api.get("mr_unitsLettingPool"))
    # last updated: API timestamp (ISO or "15 Nov 2026 23:00:05")
    last_updated = api.get("timestamp")
    if last_updated:
        last_updated = str(last_updated)
    url = build_listing_url(api, lid)
    return {
        "id": f"theonsitemanager-com-au-{lid}",
        "name": f"{suburb} {state} #{lid}" if suburb else f"QLD #{lid}",
        "region": suburb or "QLD",
        "price": price,
        "unit_price": unit_price,
        "price_source": "api_price" if price is not None else None,
        "net_income": net,
        "multiplier": None,
        "bc_percent": None,
        "contract_years": contract,
        "pool_units": pool,
        "weekly_rent_per_unit": None,
        "status": "active",
        "url": url,
        "source": "theonsitemanager.com.au",
        "notes": "",
        "risks": "",
        "action": "",
        "last_updated": last_updated,
        "last_fetched": None,
        "quality_score": None,
        "business_price": business,
        "ni_kind": (api.get("takingsBasis") or "").lower() or None,
        "_bc_salary": bc_salary,
        "_price_view": price_view,
    }


def enrich(rec, now_iso, today):
    """Compute multiplier/BC%/ROI, notes, risks, quality score."""
    price = rec.get("price")
    business = rec.get("business_price") or price
    net = rec.get("net_income")
    bc_salary = rec.pop("_bc_salary", None)
    rec.pop("_price_view", None)

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

    parts = []
    if rec["bc_percent"] is not None:
        if rec["bc_percent"] > 100:
            parts.append(f"BC {rec['bc_percent']}% — implausible: the body-corporate salary exceeds the net income, so verify the figures.")
        else:
            parts.append(f"BC {rec['bc_percent']}% "
                         f"{'healthy' if rec['bc_percent'] <= 70 else 'caution' if rec['bc_percent'] <= 80 else 'high'}.")
    if rec["multiplier"] is not None:
        if rec["multiplier"] < 0:
            parts.append(f"{rec['multiplier']}x — meaningless: the included unit is worth more than the asking price, so verify the figures.")
        else:
            parts.append(f"{rec['multiplier']}x — "
                         f"{'excellent value' if rec['multiplier'] <= 5 else 'fair' if rec['multiplier'] <= 6.5 else 'overpriced'}.")
    if not rec.get("net_income"):
        parts.append("Net income not disclosed by the broker — multiplier and ROI can't be calculated.")
    if rec.get("contract_years") is not None:
        parts.append(f"{rec['contract_years']}yr contract — "
                     f"{'good' if rec['contract_years'] >= 20 else 'adequate' if rec['contract_years'] >= 10 else 'short'}.")
    else:
        parts.append("Contract years not published by the broker.")
    if rec.get("pool_units") is not None:
        parts.append(f"{rec['pool_units']} pool units — "
                     f"{'good diversification' if rec['pool_units'] >= 30 else 'adequate pool' if rec['pool_units'] >= 15 else 'thin pool'}.")
    else:
        parts.append("Letting pool size not published by the broker.")
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
    rec["risks"] = " ".join(risks)

    # --- unverified, not deleted. A record with no usable price or
    # net income (e.g. price not published) is unverified, NOT active
    # — v2 counted such records active, which hid them from the
    # dashboard's unverified flagging.
    if not price or not net:
        rec["status"] = "unverified"
        rec["action"] = "Verify details with broker — price/income not published."
        if not rec["notes"]:
            rec["notes"] = "Details unavailable — verify with broker."
    elif rec.get("pool_units") == 0:
        rec["action"] = "Verify pool unit schedule."

    # --- implausible figures: do not let a bad parse top the rankings
    # ROI over ~40% is almost always a mis-parsed net income or an
    # EOI figure used as a price (e.g. the Brisbane City record at
    # $1,600,000 / net $1,500,000, 1.07x, ROI 93.8%, which was also
    # no longer on the broker site). Flag it and keep it out of
    # recommendations until a human verifies it.
    if roi is not None and roi > 40:
        rec["status"] = "unverified"
        rec["notes"] = (rec["notes"] + " Figures look implausible "
                        f"(ROI {roi:.1f}%) — verify with broker before relying on this.").strip()
        rec["action"] = "Verify figures with broker — ROI over 40% is not credible."

    # --- negative multiplier: the included unit is worth more than the
    # asking price, so business_price is negative and the multiplier is
    # meaningless (e.g. Caloundra #21160550: unit $750,000 > price
    # $450,000 → −2.13x). Never rank it as "excellent value".
    if rec["multiplier"] is not None and rec["multiplier"] < 0:
        rec["status"] = "unverified"
        rec["notes"] = (rec["notes"] + " Figures look implausible "
                        "(negative multiplier — unit value exceeds asking price) — verify with broker before relying on this.").strip()
        rec["action"] = "Verify figures with broker — negative multiplier (unit value exceeds asking price)."

    # --- BC% over 100: the body-corporate salary cannot exceed the net
    # income, so one of the two figures is a parse error (e.g. Surfers
    # Paradise #21151694 at 107.3%; worst case #21179119 at 10600% on a
    # $1 net income). Never treat it as merely "high".
    if rec["bc_percent"] is not None and rec["bc_percent"] > 100:
        rec["status"] = "unverified"
        rec["notes"] = (rec["notes"] + " Figures look implausible "
                        f"(BC% {rec['bc_percent']:.1f}% — BC salary exceeds net income) — verify with broker before relying on this.").strip()
        rec["action"] = "Verify figures with broker — BC% over 100% (BC salary exceeds net income)."

    score = 0
    for field in ("price", "net_income", "bc_percent", "contract_years", "pool_units"):
        if rec.get(field) is not None:
            score += 20
    if rec["multiplier"] is not None and 0 < rec["multiplier"] <= 5:
        score += 15
    elif rec["multiplier"] is not None and 0 < rec["multiplier"] <= 6.5:
        score += 10
    if rec.get("contract_years") and rec["contract_years"] >= 20:
        score += 10
    rec["quality_score"] = min(score, 125)
    return rec


def mark_duplicates(records):
    """Flag listings that share suburb + price + net income with another
    listing — usually the same property listed twice (often with a
    different included unit, hence a different multiplier). Every member
    of the group is flagged; the dashboard keeps one copy and shows a
    'possible duplicate' badge on it. Returns the number of records
    flagged."""
    import re
    groups = {}
    for r in records:
        m = re.match(r"^(.+?) QLD", r.get("name") or "")
        sub = m.group(1) if m else (r.get("name") or "")
        key = (sub, r.get("price"), r.get("net_income"))
        groups.setdefault(key, []).append(r)
    flagged = 0
    for members in groups.values():
        if len(members) < 2:
            continue
        for r in members:
            r["dup"] = True
            r["dup_count"] = len(members)
            others = ", ".join("#" + str(x["id"].split("-")[-1]) for x in members if x is not r)
            note = (f"Possible duplicate: another listing with the same suburb, price and net income exists "
                    f"({others}) — check they are not the same property before relying on either.")
            if note not in (r.get("notes") or ""):
                r["notes"] = ((r.get("notes") or "") + " " + note).strip()
            flagged += 1
    return flagged


def main():
    ap = argparse.ArgumentParser(description="Refresh PMR listings data")
    ap.add_argument("--limit", type=int, default=0, help="max listings to fetch (0 = all)")
    ap.add_argument("--dry-run", action="store_true", help="discover only, do not write files")
    ap.add_argument("--delay", type=float, default=0.3, help="seconds between requests")
    ap.add_argument("--out", default="pmr-data-latest.json")
    args = ap.parse_args()

    brisbane = timezone(timedelta(hours=10))
    now = datetime.now(brisbane)
    now_iso = now.isoformat()
    today = now.strftime("%Y-%m-%d")

    session = requests.Session()
    print("Fetching listings from the broker API…")
    raw = discover_records(session, delay=args.delay)
    print(f"API returned {len(raw)} records")
    qld = [r for r in raw if (r.get("state") or "").upper() == "QLD"]
    print(f"Queensland: {len(qld)} records")
    if args.dry_run:
        for r in qld[:20]:
            print(f"  {r.get('pageId')} {r.get('suburb')} "
                  f"{r.get('priceView')} net {r.get('takings')}")
        return 0

    records, seen = [], set()
    items = qld
    if args.limit:
        items = items[:args.limit]
    # --- NEW-badge tracking: first_seen per listing, carried forward
    # from the previous data file so a listing is NEW for 3 days after
    # it first appears (not 3 days after every run — last_fetched is
    # refreshed for all listings on every run, which made the old
    # badge show on everything).
    prev_first_seen = {}
    try:
        with open(args.out) as f:
            prev = json.load(f)
        prev_list = prev if isinstance(prev, list) else prev.get("listings", [])
        for r in prev_list:
            if r.get("id") and r.get("first_seen"):
                prev_first_seen[r["id"]] = r["first_seen"]
    except (FileNotFoundError, json.JSONDecodeError, AttributeError):
        prev_first_seen = {}
    print(f"Previous data: {len(prev_first_seen)} listings with first_seen")
    for api in items:
        lid = str(api.get("pageId") or api.get("id"))
        if lid in seen:
            continue
        seen.add(lid)
        rec = enrich(map_record(api), now_iso, today)
        # first_seen: carried forward when seen before; otherwise the
        # broker's own timestamp date (bootstrap only), else today.
        # Clamp a future date to today (timezone skew in timestamps).
        rid = rec["id"]
        if rid in prev_first_seen:
            rec["first_seen"] = prev_first_seen[rid]
        else:
            boot = parse_date(rec.get("last_updated"))
            rec["first_seen"] = boot if boot and boot <= today else today
        # NEW for 3 days: the day it first appears + the next 2 days.
        try:
            age = (now.date() - datetime.strptime(rec["first_seen"], "%Y-%m-%d").date()).days
        except ValueError:
            age = 99
        rec["is_new"] = 0 <= age < 3
        records.append(rec)

    dup_count = mark_duplicates(records)
    print(f"Possible duplicates: {dup_count} records flagged")

    records.sort(key=lambda r: (r.get("multiplier") is None,
                                r.get("multiplier") or 999))
    with open(args.out, "w") as f:
        json.dump(records, f, indent=2)
    meta = {
        "generated_at": now_iso,
        "generated_at_brisbane": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "source": "theonsitemanager.com.au api/v1/listings.php",
        "total_records": len(records),
        "active": sum(1 for r in records if r["status"] == "active"),
        "unverified": sum(1 for r in records if r["status"] == "unverified"),
        "new": sum(1 for r in records if r.get("is_new")),
        "duplicates": dup_count,
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
