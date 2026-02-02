# part2/src/peek_input.py
from pathlib import Path
import pandas as pd

def main():
    root = Path(__file__).resolve().parents[2]  # repo root
    inp = root / "part2" / "input"

    # grab the first .xlsx in input folder
    files = list(inp.glob("*.xlsx"))
    if not files:
        raise FileNotFoundError(f"No .xlsx found in {inp}")

    xlsx_path = files[0]
    print("Reading:", xlsx_path)

    df = pd.read_excel(xlsx_path)
    print("\nRows:", len(df))
    print("Columns:", list(df.columns))

    print("\nSample rows (first 3):")
    print(df.head(3).to_string(index=False))

if __name__ == "__main__":
    main()
