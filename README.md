# Curated Restaurant Discovery

This repository contains an early-stage restaurant discovery and curation pipeline designed to surface newly opened local venues that are often missed by large, global recommendation platforms.

The project combines **data discovery**, **metadata enrichment**, and **transparent, rule-based curation** to explore how quality-focused, local-first recommendations can be built in a scalable and auditable way.

While the current implementation focuses on Finland, the approach is intentionally modular and adaptable to other markets.

---

## Project Overview

The system is split into two complementary modules:

### 1. Discovery & Enrichment
A Python-based pipeline that:
- Identifies newly opened restaurants from delivery platforms
- Filters out chains and blocked brands
- Enriches candidates with public place metadata (e.g. location, categories, review counts)
- Outputs structured CSV data for further analysis or curation

This stage focuses on **finding signal early**, before venues are widely ranked or promoted elsewhere.

---

### 2. Curation Heuristics (Rule-Based Labeling)
A separate module that applies transparent, human-readable rules to label content as “recommendation-like.”

The goal is to:
- Encode subjective judgment into explicit, testable logic
- Keep curation decisions explainable and auditable
- Establish a baseline for future ML or LLM-assisted approaches

This module is intentionally rule-based to prioritize clarity over automation.

---

## Why This Exists

Most restaurant discovery platforms optimize for scale, popularity, and global coverage.  
That often means smaller local venues, especially in markets like Finland, are surfaced late or not at all.

This project explores an alternative direction:
- **Local-first instead of global-first**
- **Quality over volume**
- **Human taste supported by data, not replaced by it**

---

## Repository Structure

```text
src/                    # Discovery & enrichment pipeline
  ├── main.py
  ├── wolt_scrape.py
  ├── places_enrich.py
  └── config/

curation_rules/         # Rule-based labeling logic
  ├── rules.py
  └── label_recommendations.py

data/                   # Generated CSV outputs
docs/                   # Notes and supporting documentation


