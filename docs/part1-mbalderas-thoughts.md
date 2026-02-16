## Part 1  Discovery & Enrichment

This module focuses on discovering newly opened local restaurants and enriching them with structured place data.

The starting point is Wolt’s list of new restaurants in Helsinki. Because large chains and franchises tend to appear first, a `blocklist.txt` is used to exclude venues that do not align with the World of Mouth (WoM) vision.

The pipeline begins with a lightweight scraping step to collect restaurant names, followed by enrichment using the Google Places API. This approach ensures accurate address data and consistent place metadata that could not be reliably extracted through scraping alone.

To keep the output focused, only a curated subset of place tags is retained. An allowlist is applied so that irrelevant or noisy tags are excluded from the final dataset.

Since the goal is to surface *new or early-stage* venues, an additional filter keeps only restaurants with fewer than 100 Google reviews. This threshold is a heuristic rather than a strict rule and is expected to vary by city or market.

Because there is no reliable way to determine exact opening dates from these data sources, the pipeline is designed to generate **high-signal candidates**, not guaranteed “opened in the last X months” results. Precision improves over time as the blocklist and tag filters are refined.

The output is a CSV containing:
- Restaurant name
- Full address
- Place description
- Curated tags
