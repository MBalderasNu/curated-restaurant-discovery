# part2/src/label_recommendations.py
from pathlib import Path
import pandas as pd

from rules import decision_rules


def main():
    root = Path(__file__).resolve().parents[2]  # repo root
    inp_dir = root / "part2" / "input"
    out_dir = root / "part2" / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    # use the first .xlsx in input
    files = list(inp_dir.glob("*.xlsx"))
    if not files:
        raise FileNotFoundError(f"No .xlsx found in {inp_dir}")

    xlsx_path = files[0]
    print("Reading:", xlsx_path)

    df = pd.read_excel(xlsx_path)

    # expected columns (from your peek)
    col_name = "Restaurant → Name"
    col_comment = "Comment"
    col_image = "Image yes/no"
    col_created = "Created At"
    col_tags = "Tags"

    missing = [c for c in [col_name, col_comment, col_image, col_created, col_tags] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in input: {missing}. Found: {list(df.columns)}")

    preds = []
    confs = []
    reasons = []

    for _, row in df.iterrows():
        name = row.get(col_name, "")
        comment = row.get(col_comment, "")
        image = row.get(col_image, "")
        tags = row.get(col_tags, "")

        label, confidence, reason_codes = decision_rules(
            restaurant_name=str(name) if name is not None else "",
            comment=str(comment) if comment is not None else "",
            image_yes_no=str(image) if image is not None else "",
            tags=str(tags) if tags is not None else "",
        )

        preds.append(label)
        confs.append(confidence)
        reasons.append(", ".join(reason_codes))

    out_df = df.copy()
    out_df["Predicted decision"] = preds
    out_df["Confidence"] = confs
    out_df["Reason codes"] = reasons

    out_path = out_dir / "recommendations_labeled.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"✅ Wrote {len(out_df)} rows -> {out_path}")


if __name__ == "__main__":
    main()
