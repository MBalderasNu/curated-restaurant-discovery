# src/main.py
from pathlib import Path
import re
import csv
import os

from dotenv import load_dotenv

from wolt_scrape import fetch_newest_venues
from places_enrich import enrich_place


MAX_REVIEWS = 100  # your rule/this means a restaurant can not have more than this amount of reviews to be kept. 


def norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s)  # remove punctuation
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_blocked(venue_name: str, blocked_list: list[str]) -> bool:
    v = norm(venue_name)
    for b in blocked_list:
        bn = norm(b)
        if not bn:
            continue
        if v == bn or v.startswith(bn + " ") or v.startswith(bn):
            return True
    return False


def main():
    load_dotenv()

    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GOOGLE_PLACES_API_KEY. Add it to your .env file.")

    root = Path(__file__).resolve().parents[1]
    blocklist_path = root / "config" / "blocklist.txt"

    out_csv = root / "data" / "helsinki_new_openings.csv"
    debug_csv = root / "data" / "helsinki_new_openings_debug.csv"
    out_csv.parent.mkdir(exist_ok=True)

    blocked = []
    if blocklist_path.exists():
        blocked = [
            ln.strip()
            for ln in blocklist_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]

    venues = fetch_newest_venues(limit=30)

    print(f"Loaded {len(blocked)} blocked brands")
    print(f"Wolt venues: {len(venues)} (see debug CSV for kept/blocked breakdown)")

    rows = []
    debug_rows = []

    for i, v in enumerate(venues, start=1):
        # 1) blocklist filter
        if is_blocked(v.name, blocked):
            debug_rows.append(
                {
                    "wolt_name": v.name,
                    "wolt_url": v.url,
                    "places_name": "",
                    "full_address": "",
                    "reviews_total": "",
                    "tags": "",
                    "reason": "blocked_brand",
                }
            )
            continue

        # 2) Places enrichment
        print(f"[{i}/{len(venues)}] Enriching: {v.name}")
        enriched = enrich_place(api_key, v.name, city="Helsinki")
        if not enriched:
            debug_rows.append(
                {
                    "wolt_name": v.name,
                    "wolt_url": v.url,
                    "places_name": "",
                    "full_address": "",
                    "reviews_total": "",
                    "tags": "",
                    "reason": "no_places_match",
                }
            )
            continue

        if not enriched.formatted_address:
            debug_rows.append(
                {
                    "wolt_name": v.name,
                    "wolt_url": v.url,
                    "places_name": enriched.name,
                    "full_address": "",
                    "reviews_total": enriched.user_ratings_total,
                    "tags": ", ".join(enriched.tags),
                    "reason": "missing_address",
                }
            )
            continue

        # 3) review-count filter
        if enriched.user_ratings_total > MAX_REVIEWS:
            debug_rows.append(
                {
                    "wolt_name": v.name,
                    "wolt_url": v.url,
                    "places_name": enriched.name,
                    "full_address": enriched.formatted_address,
                    "reviews_total": enriched.user_ratings_total,
                    "tags": ", ".join(enriched.tags),
                    "reason": f"too_many_reviews(>{MAX_REVIEWS})",
                }
            )
            continue

        # keep
        rows.append(
            {
                "name": enriched.name,
                "full_address": enriched.formatted_address,
                "description": enriched.description,
                "tags": ", ".join(enriched.tags),
            }
        )
        debug_rows.append(
            {
                "wolt_name": v.name,
                "wolt_url": v.url,
                "places_name": enriched.name,
                "full_address": enriched.formatted_address,
                "reviews_total": enriched.user_ratings_total,
                "tags": ", ".join(enriched.tags),
                "reason": "kept",
            }
        )

    # de-dupe final output by (name, address)
    uniq = {}
    for r in rows:
        key = (r["name"].lower(), r["full_address"].lower())
        uniq[key] = r
    final_rows = list(uniq.values())

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["name", "full_address", "description", "tags"])
        w.writeheader()
        w.writerows(final_rows)

    with open(debug_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "wolt_name",
                "wolt_url",
                "places_name",
                "full_address",
                "reviews_total",
                "tags",
                "reason",
            ],
        )
        w.writeheader()
        w.writerows(debug_rows)

    kept_count = sum(1 for r in debug_rows if r["reason"] == "kept")
    blocked_count = sum(1 for r in debug_rows if r["reason"] == "blocked_brand")
    not_kept_count = len(debug_rows) - kept_count

    print(f"Wrote {len(final_rows)} rows -> {out_csv}")
    print(
        f"Debug rows: {len(debug_rows)} | Kept: {kept_count} | "
        f"Blocked: {blocked_count} | Not kept: {not_kept_count} -> {debug_csv}"
    )
    print("Debug output includes blocked venues + reason codes -> data/helsinki_new_openings_debug.csv")


if __name__ == "__main__":
    main()
