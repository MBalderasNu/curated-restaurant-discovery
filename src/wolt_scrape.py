from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# This version returns actual HTML venue names (server-rendered)
WOLT_NEWEST_URL = "https://wolt.com/en/fin/helsinki/newest-venues?srsltid=AfmBOopGqbrOIW8EQnDKEZrjaizPsC9xYEdDc25SX57vFcOFspXHMn3-"
BASE = "https://wolt.com"

@dataclass
class WoltVenue:
    name: str
    url: str

def fetch_newest_venues(limit: int = 50) -> List[WoltVenue]:
    r = requests.get(
        WOLT_NEWEST_URL,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"},
    )
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    venues: List[WoltVenue] = []

    for a in soup.select('a[href*="/helsinki/restaurant/"]'):
        name = (a.get_text() or "").strip()
        href = a.get("href") or ""
        if not name or not href:
            continue

        url = urljoin(BASE, href)
        venues.append(WoltVenue(name=name, url=url))

    # de-dupe by URL
    seen = set()
    out = []
    for v in venues:
        if v.url not in seen:
            seen.add(v.url)
            out.append(v)

    return out[:limit]
