# src/places_enrich.py
from dataclasses import dataclass
from typing import Optional, List, Set
import re
import requests


ALLOWED_TAGS = {
    # your original tags
    "street food", "asian", "chicken", "gyros", "american", "mexican", "wings", "bbq",
    "mediterranean", "falafel", "fish", "meat & fish", "japanese", "fine dining", "nordic",
    "great wine list", "cafe", "bakery", "Café & bakery", "Wine bar", "Brunch", "Natural wine",
    "Casual", "Pizza", "Italian", "Families", "Local", "Walk-in", "Lunch", "Take away",
    "Counter seating", "New opening", "Vegetarians", "Vegans", "Cheap eats", "Family friendly",
    "Pet friendly", "Dinner", "Chinese", "Terrace",

    # added tags
    "Cocktail bar", "Craft beer", "Desserts", "Middle Eastern", "Korean", "Date night",
}

# Map Google place "types" -> your tags
TYPE_TO_TAGS = {
    "restaurant": {"Casual", "Dinner"},
    "bar": set(),  # don't assume wine bar
    "cafe": {"cafe"},
    "bakery": {"bakery"},
    "meal_takeaway": {"Take away"},
}

KEYWORD_TO_TAGS = [
    (r"\bpizza\b", {"Pizza"}),
    (r"\bitalian\b|\btrattoria\b|\bosteria\b", {"Italian"}),
    (r"\bkebab\b|\bdöner\b|\bdoner\b|\bgyro\b|\bgyros\b", {"street food", "gyros", "Middle Eastern"}),
    (r"\bfalafel\b", {"falafel", "mediterranean", "street food", "Middle Eastern"}),
    (r"\bburger\b|\bbrgr\b", {"american", "Casual"}),
    (r"\bwings\b", {"wings"}),
    (r"\bbbq\b|\bbarbecue\b|\bsmokehouse\b", {"bbq"}),
    (r"\btaco\b|\bburrito\b|\btaqueria\b", {"mexican"}),
    (r"\bsushi\b|\bizakaya\b|\bramen\b|\btempura\b|\bshokudo\b", {"japanese", "asian"}),
    (r"\bchinese\b|\bnoodle\b|\bdumpling\b|\bhot\s?pot\b", {"Chinese", "asian"}),
    (r"\bkorean\b|\bbibimbap\b|\bbulgogi\b|\bkimchi\b|\bk-fry\b", {"Korean", "asian"}),
    (r"\bviet\b|\bpho\b|\bbanh\s?mi\b", {"asian"}),

    (r"\bmatcha\b", {"asian", "cafe", "Desserts"}),
    (r"\bcafe\b|\bcafé\b", {"cafe"}),
    (r"\bbakery\b|\bpatisserie\b", {"bakery", "Desserts"}),
    (r"\bdessert\b|\bgelato\b|\bice\s?cream\b|\bchocolate\b", {"Desserts"}),

    (r"\bcocktail\b|\bmixology\b", {"Cocktail bar"}),
    (r"\btaproom\b|\bbrew\b|\bbrewery\b|\bcraft\b", {"Craft beer"}),

    (r"\bfine dining\b|\bchef's table\b|\btasting menu\b", {"fine dining", "Date night"}),

    (r"\bbrunch\b", {"Brunch"}),
    (r"\bwine\b", {"Wine bar"}),
]


@dataclass
class PlacesResult:
    name: str
    formatted_address: str
    description: str
    tags: List[str]
    user_ratings_total: int


def find_place_id(api_key: str, query: str) -> Optional[str]:
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "key": api_key,
        "input": query,
        "inputtype": "textquery",
        "fields": "place_id",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    cands = data.get("candidates", [])
    if not cands:
        return None
    return cands[0].get("place_id")


def get_place_details(api_key: str, place_id: str) -> Optional[dict]:
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "key": api_key,
        "place_id": place_id,
        "fields": "name,formatted_address,types,editorial_summary,user_ratings_total",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("result")


def _infer_tags(name: str, types: List[str]) -> List[str]:
    tags: Set[str] = set()
    tags.add("New opening")

    for t in (types or []):
        tags.update(TYPE_TO_TAGS.get(t, set()))

    low = (name or "").lower()
    for pattern, mapped_tags in KEYWORD_TO_TAGS:
        if re.search(pattern, low):
            tags.update(mapped_tags)

    if "cafe" in tags and "bakery" in tags:
        tags.discard("cafe")
        tags.discard("bakery")
        tags.add("Café & bakery")

    return [t for t in sorted(tags) if t in ALLOWED_TAGS]


def enrich_place(api_key: str, venue_name: str, city: str = "Helsinki") -> Optional[PlacesResult]:
    place_id = find_place_id(api_key, f"{venue_name}, {city}")
    if not place_id:
        return None

    d = get_place_details(api_key, place_id)
    if not d:
        return None

    name = (d.get("name") or venue_name).strip()
    addr = (d.get("formatted_address") or "").strip()

    editorial = d.get("editorial_summary") or {}
    desc = ""
    if isinstance(editorial, dict):
        desc = (editorial.get("overview") or "").strip()
    if not desc:
        desc = "New venue in Helsinki (via Wolt discovery)."

    types = d.get("types") or []
    tags = _infer_tags(name=name, types=types)

    urt = int(d.get("user_ratings_total") or 0)

    return PlacesResult(
        name=name,
        formatted_address=addr,
        description=desc,
        tags=tags,
        user_ratings_total=urt,
    )
