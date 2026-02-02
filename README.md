# WoM New Openings (Helsinki)

Pulls newest venues from Wolt (Helsinki), filters out blocked brands, enriches with Google Places, and outputs a CSV.

## Setup
1) Create venv
2) Install deps
3) Add API key
4) Run

### venv
python -m venv .venv

### activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

### install
pip install -r requirements.txt

### env
Copy `.env.example` -> `.env` and fill `GOOGLE_PLACES_API_KEY`.

## Run
python src/main.py
