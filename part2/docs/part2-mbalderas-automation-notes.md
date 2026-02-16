## Part 2 — Curation Heuristics (Rule-Based Labeling)

This module labels restaurant recommendations using practical, transparent quality rules based on World of Mouth (WoM) guidelines, combined with my own curation preferences around clarity, specificity, and trust.

The aim is to translate subjective judgment into explicit, auditable logic that can be reviewed, refined, and later extended.

---

### How it works

The script evaluates each recommendation in stages, from clear disqualifiers to more nuanced quality signals.

**Hard removals**  
Recommendations are removed if they clearly do not fit WoM guidelines:
- Chains or franchises
- Hotels (not a target venue type)
- Empty or near-empty comments
- Non-English recommendations
- Negative recommendations (warnings, “avoid this”, etc.)
- Marketing-style or AI-like content that is overly polished, hype-driven, or lacks real experience detail

**Needs improvement**  
Recommendations that contain value but require cleanup are flagged:
- Excessive emoji use
- Dash-heavy or list-style formatting
- Messy writing (excess punctuation or chaotic structure)
- Overly positive praise without concrete details

**Weak signal handling**  
When supporting signals are limited:
- No image + short or vague text → *Needs more information*
- Text below minimum length without strong specifics → *Remove*
- Short, low-specificity comments → *Needs more information*

**Keep**  
Recommendations are kept when they read like a genuine friend-to-friend suggestion, including:
- What to order
- What makes the place special
- Concrete experience details written in a natural, human voice

---

### How to run

From the project root:

```bash
pip install -r requirements.txt
python part2/src/label_recommendations.py
