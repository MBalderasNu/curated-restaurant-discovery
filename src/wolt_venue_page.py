# src/wolt_venue_page.py
from dataclasses import dataclass
from typing import Optional, Any
import json
import re

import requests
from bs4 import BeautifulSoup


@dataclass
class VenueDetails:
    address: str
    description: str


def _is_bad_address(s: str) -> bool:
    s = (s or "").strip()
    return (not s) or bool(re.fullmatch(r"\d+", s))  # "0", "12", etc.


def _clean(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _walk_find_strings(obj: Any, keys_hint: set[str]) -> list[str]:
    """
    Recursively collect candidate strings from a big JSON object.
    If a dict key matches hints (like 'address', 'description'), we prioritize its values.
    """
    found: list[str] = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            lk = str(k).lower()
            if lk in keys_hint:
                if isinstance(v, str):
                    found.append(v)
                else:
                    found.extend(_walk_find_strings(v, keys_hint))
            else:
                found.extend(_walk_find_strings(v, keys_hint))

    elif isinstance(obj, list):
        for item in obj:
            found.extend(_walk_find_strings(item, keys_hint))

    elif isinstance(obj, str):
        found.append(obj)

    return found


def _pick_address(candidates: list[str]) -> str:
    for c in candidates:
        c = _clean(c)
        if _is_bad_address(c):
            continue

        low = c.lower()

        # skip opening hours like "Mo 10:30-24:00"
        if re.match(r"^(mo|tu|we|th|fr|sa|su)\s+\d{1,2}:\d{2}", low):
            continue
        if ":" in c and "-" in c and len(c) <= 20:
            continue

        # skip urls
        if "http" in low or "imageproxy" in low:
            continue

        # require it to look like a real address (postal code, comma, or Helsinki)
        has_postcode = bool(re.search(r"\b\d{5}\b", c))
        has_city = "helsinki" in low
        has_comma = "," in c

        if any(ch.isdigit() for ch in c) and any(ch.isalpha() for ch in c) and (has_postcode or has_city or has_comma):
            return c

    return ""


def _pick_description(candidates: list[str]) -> str:
    for c in candidates:
        c = _clean(c)
        if not c or len(c) < 20 or len(c) > 260:
            continue

        low = c.lower()

        # skip urls and image assets
        if "http" in low or "imageproxy" in low or low.endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue

        # skip UI/system text
        if "machine translation" in low:
            continue
        if any(bad in low for bad in ["cookies", "privacy", "sign in", "log in"]):
            continue

        return c

    return ""


def fetch_venue_details(url: str) -> Optional[VenueDetails]:
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    address = ""
    description = ""

    # 1) Try JSON-LD first (schema.org)
    for s in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(s.get_text(strip=True) or "{}")
        except Exception:
            continue

        addr_candidates = _walk_find_strings(data, {"address", "streetaddress", "formatted_address"})
        desc_candidates = _walk_find_strings(data, {"description"})
        address = address or _pick_address(addr_candidates)
        description = description or _pick_description(desc_candidates)

        if address and description:
            break

    # 2) Fallback: parse __NEXT_DATA__ (Wolt often uses Next.js)
    if not address or not description:
        next_data = soup.find("script", attrs={"id": "__NEXT_DATA__"})
        if next_data:
            try:
                data = json.loads(next_data.get_text(strip=True) or "{}")

                addr_candidates = _walk_find_strings(
                    data,
                    {"address", "streetaddress", "formatted_address", "venueaddress", "deliveryaddress"},
                )
                desc_candidates = _walk_find_strings(
                    data,
                    {"description", "shortdescription", "summary", "about"},
                )

                address = address or _pick_address(addr_candidates)
                description = description or _pick_description(desc_candidates)
            except Exception:
                pass

    if _is_bad_address(address):
        address = ""

    if not address and not description:
        return None

    return VenueDetails(address=address, description=description)
