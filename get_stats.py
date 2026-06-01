import argparse
from pathlib import Path

import pandas as pd

import topic_comparison


def read_csv_with_fallback(path: Path, encodings=None) -> pd.DataFrame:
    encodings = encodings or ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    last_error = None
    for encoding in encodings:
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Could not read CSV file: {path}")


def detect_keyword_column(df: pd.DataFrame) -> str:
    candidates = ["keywords", "keyword_group", "keyword", "cluster", "word_group", "terms"]
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return df.columns[0]


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Read a CSV with keyword groups and compute outlet-specific article match proportions "
            "for each row using topic_comparison.keyword_group_outlet_scores."
        )
    )
    parser.add_argument("input_csv", type=Path, help="Path to the input CSV file")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output CSV path. Defaults to <input>_scores.csv",
    )
    parser.add_argument(
        "--keyword-column",
        type=str,
        default=None,
        help=(
            "Column containing the keyword group. Defaults to 'keywords' if present, "
            "otherwise the first column."
        ),
    )
    args = parser.parse_args()

    df = read_csv_with_fallback(args.input_csv)
    keyword_col = args.keyword_column or detect_keyword_column(df)

    if keyword_col not in df.columns:
        raise KeyError(f"Keyword column '{keyword_col}' not found in {args.input_csv}")

    results = []
    for idx, row in df.iterrows():
        raw_value = row[keyword_col]
        if pd.isna(raw_value):
            keywords = []
        else:
            keywords = [token.strip() for token in str(raw_value).split(",") if token.strip()]

        outlet_scores = topic_comparison.keyword_group_outlet_scores(keywords)
        row_record = row.to_dict()
        row_record["keyword_group"] = str(raw_value)
        row_record["kesma_proportion"] = outlet_scores["kesma"]
        row_record["independent_proportion"] = outlet_scores["independent"]
        results.append(row_record)

    output_df = pd.DataFrame(results)

    if args.output is None:
        output_path = args.input_csv.with_name(f"{args.input_csv.stem}_scores.csv")
    else:
        output_path = args.output

    output_df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Wrote {len(output_df)} scores to {output_path}")


if __name__ == "__main__":
    main()
