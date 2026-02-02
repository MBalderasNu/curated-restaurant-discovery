# WoM Case Assignment (Parts 1 & 2)

This repo contains my World of Mouth case assignment work.

## What’s inside

### Part 1 – New Openings (Helsinki)
Pulls newest venues from Wolt (Helsinki), filters out blocked brands, enriches with Google Places (address + types + review count), applies simple heuristics, and outputs CSV.

Important files:
- `src/main.py` (runner)
- `src/wolt_scrape.py` (Wolt discovery)
- `src/places_enrich.py` (Google Places enrichment)
- `config/blocklist.txt` (blocked brands/franchises)
- `config/tags.txt` (allowed tags)

Outputs:
- `data/helsinki_new_openings.csv` (final)
- `data/helsinki_new_openings_debug.csv` (debug/validation)

### Part 2 – Recommendation Flagging
Reads the provided Excel dataset, applies rule-based labeling, and outputs a labeled CSV.

Important files:
- `part2/src/label_recommendations.py` (runner)
- `part2/src/rules.py` (rule logic)
- `part2/input/` (put the Excel file here)
- `part2/output/recommendations_labeled.csv` (output)

Docs:
- `docs/` contains my written background for Parts 1–3 (used for the final submission PDF).

## Quick start (Windows PowerShell)

From the project root, run this once:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; copy .env.example .env


## Run Part 1 (New Openings)
```powershell
python src\main.py



## Run Part 2 (Recommendation Flagging)
```powershell
python part2\src\label_recommendations.py

