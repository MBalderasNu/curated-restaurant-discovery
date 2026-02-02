# part2/src/rules.py
import re
from typing import List, Tuple

LABEL_KEEP = "Keep"
LABEL_REMOVE = "Remove"
LABEL_NEEDS_INFO = "Needs more information"
LABEL_NEEDS_EDIT = "Recommendation needs editing"

MIN_CHARS = 42  # WoM app minimum
MAX_EMOJIS = 2

# Hard threshold: if emoji spam + hype template/format spam -> remove
HARD_EMOJI_REMOVE = 3

# Common UK spellings we don't want to flag as "misspelled"
UK_OK_WORDS = {
    "favourite", "colour", "flavour", "neighbourhood", "theatre", "centre",
    "travelling", "traveller", "apologise", "organise", "realise", "behaviour",
    "cheque", "grey", "cheers",
}

# Common food/restaurant-related typos we *do* want to flag for editing
COMMON_FOOD_TYPOS = {
    "napoletan",  # likely intended "neapolitan" / "napoletana/o"
}

# AI-ish hype template phrases (not perfect, but catches the vibe)
AI_HYPE_PHRASES = [
    "culinary gem",
    "perfect harmony",
    "work of art",
    "beautifully crafted",
    "unforgettable flavors",
    "unforgettable flavours",
    "thoughtful presentation",
    "highly recommended",
    "must-try",
    "must try",
]


# --- spelling / typo detection (lightweight) ---
try:
    from spellchecker import SpellChecker
    _SPELL = SpellChecker(language="en")
except Exception:
    _SPELL = None


def norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def startswith_any(name: str, prefixes: List[str]) -> bool:
    n = norm(name)
    for p in prefixes:
        pn = norm(p)
        if not pn:
            continue
        if (
            n == pn
            or n.startswith(pn + " ")
            or n.startswith(pn + "-")
            or n.startswith(pn + "’")
            or n.startswith(pn + "'")
        ):
            return True
    return False


def has_obvious_typos(text: str) -> bool:
    """
    Catch super obvious typos without a dictionary:
    - 3+ same letter in a row (ex: 'excelllent')
    - long word with no vowels (rare but good signal)
    Also flags COMMON_FOOD_TYPOS immediately.
    """
    if not text:
        return False
    words = re.findall(r"[A-Za-z']+", text)
    for w in words:
        wl = w.lower()
        if wl in COMMON_FOOD_TYPOS:
            return True
        if re.search(r"(.)\1\1", wl):  # triple letter
            return True
        if len(wl) >= 8 and not re.search(r"[aeiouy]", wl):
            return True
    return False


def has_spelling_issues(text: str) -> bool:
    """
    Soft English spellcheck:
    - ignores short words
    - ignores words with non-ascii chars (ä/ö/å etc)
    - ignores capitalized words (often names)
    - ignores common UK spellings in UK_OK_WORDS
    Flags only when there are multiple likely mistakes.
    Also flags COMMON_FOOD_TYPOS immediately (editing).
    """
    if not text:
        return False

    if has_obvious_typos(text):
        return True

    if _SPELL is None:
        return False

    tokens = re.findall(r"[A-Za-z']+", text)
    cleaned = []
    for w in tokens:
        if len(w) < 4:
            continue
        wl = w.lower()

        if wl in UK_OK_WORDS:
            continue

        if wl in COMMON_FOOD_TYPOS:
            return True

        if any(ord(ch) > 127 for ch in w):
            continue

        if w[0].isupper():
            continue

        cleaned.append(wl)

    if len(cleaned) < 8:
        return False

    misspelled = _SPELL.unknown(cleaned)
    return len(misspelled) >= 2


# --- guardrail rules (chains / hotel / language / AI-ish tone) ---

CHAIN_PREFIXES = [
    # minimal set for Part 2 (extend anytime)
    "hesburger",
    "mcdonald",
    "mcdonald's",
    "subway",
    "burger king",
    "kfc",
    "taco bell",
    "pizza hut",
    "starbucks",
    "espresso house",
    "fazer cafe",
]


def is_chain_or_franchise(restaurant_name: str) -> bool:
    return startswith_any(restaurant_name, CHAIN_PREFIXES)


def is_hotel(restaurant_name: str) -> bool:
    n = norm(restaurant_name)
    return "hotel" in n


FINISH_MARKERS = [
    "ja", "on", "se", "että", "mutta", "kun", "tämä", "tosi", "hyvä", "ihan",
    "suosittelen", "ravintola", "kiva", "mahtava", "ruoka", "palvelu", "annos",
]

ENGLISH_MARKERS = [
    "and", "the", "is", "was", "are", "but", "this", "that", "really", "great",
    "recommend", "food", "service", "place", "try", "dish", "menu",
]


def is_non_english(comment: str) -> bool:
    """
    Lightweight language check without external libraries.
    Flags if Finnish markers strongly outweigh English markers.
    """
    t = norm(comment)
    if not t:
        return False

    fin_hits = sum(1 for w in FINISH_MARKERS if re.search(rf"\b{re.escape(w)}\b", t))
    eng_hits = sum(1 for w in ENGLISH_MARKERS if re.search(rf"\b{re.escape(w)}\b", t))

    if fin_hits >= 3 and fin_hits >= eng_hits + 2:
        return True

    if sum(t.count(ch) for ch in ["ä", "ö", "å"]) >= 3 and eng_hits == 0:
        return True

    return False


MARKETING_WORDS = [
    "culinary landscape", "philosophy", "time and place", "bounty", "showcase",
    "evolved", "shaped", "experience", "once in a lifetime", "truly", "daring",
    "concept", "vision", "period", "themes", "throughout the year", "region",
]

FIRST_PERSON = [" i ", " i'", " i'm", " my ", " we ", " our ", " us "]


def has_concrete_food(comment: str) -> bool:
    t = norm(comment)
    dish_words = [
        "pizza", "pasta", "ramen", "sushi", "tartar", "herring", "steak",
        "pancake", "dessert", "coffee", "wine", "beer", "cocktail", "cheese",
        "bread", "dumpling", "noodle", "schnapps", "vorschmack",
    ]
    return any(re.search(rf"\b{re.escape(w)}\b", t) for w in dish_words)


def is_marketing_or_ai_copy(comment: str) -> bool:
    """
    Heuristic: long + no first-person voice + marketing phrases + low concrete food detail.
    """
    t = (comment or "").strip()
    tn = norm(t)
    if not tn:
        return False

    first_person = any(fp in f" {tn} " for fp in FIRST_PERSON)
    marketing_hits = sum(1 for w in MARKETING_WORDS if w in tn)

    if len(tn) >= 140 and (not first_person) and marketing_hits >= 2 and (not has_concrete_food(tn)):
        return True

    return False


# --- style / content heuristics ---

def count_emojis(text: str) -> int:
    """
    Rough emoji counter using Unicode ranges. Not perfect, but good enough.
    """
    if not text:
        return 0
    emoji_re = re.compile(
        "["
        "\U0001F300-\U0001F5FF"
        "\U0001F600-\U0001F64F"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\u2600-\u26FF"
        "\u2700-\u27BF"
        "]+",
        flags=re.UNICODE
    )
    return len(emoji_re.findall(text))


def uses_dashy_style(text: str) -> bool:
    if not text:
        return False
    bullet_dashes = len(re.findall(r"(?m)^\s*-\s+", text))
    inline_dashes = text.count(" - ")
    return bullet_dashes >= 2 or inline_dashes >= 3


def is_generic_comment(text: str) -> bool:
    tn = norm(text)
    generic_phrases = [
        "great place", "really good", "so good", "nice place", "love it",
        "highly recommend", "amazing", "awesome", "pretty good", "must try",
    ]
    if len(tn) < MIN_CHARS and any(p in tn for p in generic_phrases):
        return True
    return False


def overly_positive_hype(text: str) -> bool:
    tn = norm(text)
    hype_words = [
        "best", "incredible", "perfect", "unreal", "life changing",
        "insane", "mind blowing", "never had better", "10/10"
    ]
    exclamations = text.count("!")
    hype_hits = sum(1 for w in hype_words if w in tn)
    return (hype_hits >= 2) or (exclamations >= 3)


def is_negative_recommendation(text: str) -> bool:
    """
    WoM guideline: negative recommendations get deleted.
    """
    tn = norm(text)

    strong_negative = [
        "avoid", "don't go", "do not go", "never again", "waste of money",
        "terrible", "awful", "horrible", "worst", "disgusting", "bad service",
        "overpriced and bad", "not worth", "would not recommend"
    ]
    positive_markers = [
        "recommend", "worth", "love", "great", "amazing", "must", "try",
        "good", "favorite", "solid"
    ]

    has_strong_neg = any(p in tn for p in strong_negative)
    has_pos = any(p in tn for p in positive_markers)

    if "avoid" in tn or "don't go" in tn or "do not go" in tn or "would not recommend" in tn:
        return True

    return has_strong_neg and not has_pos


def looks_like_needs_edit(text: str) -> bool:
    if not text:
        return False
    if re.search(r"[!?.,]{3,}", text):
        return True
    if text.count("\n") >= 6:
        return True
    return False


def has_specifics(text: str) -> bool:
    tn = norm(text)
    signals = [
        "dish", "menu", "wine", "beer", "cocktail", "tasting", "chef",
        "atmosphere", "service", "interior", "music", "book", "walk in",
        "order", "try",
        "ramen", "pizza", "pasta", "tartar", "herring", "schnapps",
        "steak", "dessert", "cheese", "bread", "coffee",
    ]
    return any(s in tn for s in signals)


def is_ai_hype_template(text: str) -> bool:
    tn = norm(text)
    hits = sum(1 for p in AI_HYPE_PHRASES if p in tn)
    return hits >= 3


# --- main decision function ---

def decision_rules(
    restaurant_name: str,
    comment: str,
    image_yes_no: str,
    tags: str,
) -> Tuple[str, str, List[str]]:
    """
    Returns: (label, confidence, reason_codes)
    confidence: high / medium / low
    """
    reasons: List[str] = []

    name = (restaurant_name or "").strip()
    text = (comment or "").strip()
    tn = norm(text)
    img = norm(image_yes_no)
    _ = tags  # intentionally ignored

    # Guardrails first
    if is_chain_or_franchise(name):
        reasons.append("chain_or_franchise")
        return (LABEL_REMOVE, "high", reasons)

    if is_hotel(name):
        reasons.append("hotel_not_target")
        return (LABEL_REMOVE, "high", reasons)

    if not tn:
        reasons.append("empty_comment")
        return (LABEL_REMOVE, "high", reasons)

    if is_non_english(text):
        reasons.append("non_english_comment")
        return (LABEL_REMOVE, "high", reasons)

    if is_marketing_or_ai_copy(text):
        reasons.append("marketing_or_ai_tone")
        return (LABEL_REMOVE, "high", reasons)

    if is_negative_recommendation(text):
        reasons.append("negative_recommendation")
        return (LABEL_REMOVE, "high", reasons)

    # Compute format/hype flags BEFORE returning early
    emoji_n = count_emojis(text)
    dashy = uses_dashy_style(text)
    hype_template = is_ai_hype_template(text) or overly_positive_hype(text)

    emoji_spam = emoji_n >= HARD_EMOJI_REMOVE

    # If hype + dash spam or hype + emoji spam -> Remove
    if hype_template and (dashy or emoji_spam):
        reasons.append("hype_plus_format_spam")
        if dashy:
            reasons.append("dashy_formatting")
        if emoji_spam:
            reasons.append(f"emoji_spam({emoji_n})")
        return (LABEL_REMOVE, "high", reasons)

    # Dashy formatting handling
    if dashy:
        reasons.append("dashy_formatting")
        if has_specifics(text):
            return (LABEL_NEEDS_EDIT, "medium", reasons)
        return (LABEL_NEEDS_INFO, "medium", reasons)

    # Emoji cap handling
    if emoji_n > MAX_EMOJIS:
        reasons.append(f"too_many_emojis({emoji_n})")
        if is_generic_comment(text):
            reasons.append("generic_hype_with_emojis")
            return (LABEL_REMOVE, "high", reasons)
        return (LABEL_NEEDS_EDIT, "medium", reasons)

    # Below platform min chars: low-signal unless it still contains specifics
    if len(tn) < MIN_CHARS and not has_specifics(text):
        reasons.append(f"below_min_chars(<{MIN_CHARS})")
        return (LABEL_REMOVE, "high", reasons)

    # Short + generic hype
    if is_generic_comment(text):
        reasons.append("generic_short_comment")
        return (LABEL_REMOVE, "high", reasons)

    # Overly positive hype without specifics (softer case)
    if overly_positive_hype(text) and not has_specifics(text):
        reasons.append("overly_positive_without_specifics")
        if len(tn) < 60:
            reasons.append("short_hype")
            return (LABEL_REMOVE, "high", reasons)
        return (LABEL_NEEDS_INFO, "medium", reasons)

    # No image raises the bar
    if img == "no" and len(tn) < 60 and not has_specifics(text):
        reasons.append("no_image_weak_text")
        return (LABEL_NEEDS_INFO, "medium", reasons)

    # Messy but salvageable
    if looks_like_needs_edit(text) and has_specifics(text):
        reasons.append("messy_but_salvageable")
        return (LABEL_NEEDS_EDIT, "medium", reasons)

    # Medium length but low specificity
    if len(tn) < 120 and not has_specifics(text):
        reasons.append("low_specificity")
        return (LABEL_NEEDS_INFO, "medium", reasons)

    # Spelling issues: if it's otherwise a good rec, flag for editing
    if has_spelling_issues(text):
        reasons.append("spelling_issues")
        return (LABEL_NEEDS_EDIT, "medium", reasons)

    # Otherwise keep
    reasons.append("specific_helpful")
    return (LABEL_KEEP, "high" if has_specifics(text) else "medium", reasons)
