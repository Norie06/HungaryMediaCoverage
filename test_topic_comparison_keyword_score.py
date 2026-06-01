import argparse
import json

import topic_comparison


def parse_keyword_group(raw_group: str) -> list[str]:
    return [token.strip() for token in raw_group.split(",") if token.strip()]


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Print outlet-specific article match proportions for a keyword group."
        )
    )
    parser.add_argument(
        "--keyword-group",
        type=str,
        default=None,
        help="Comma-separated keyword group, e.g. 'orbán, magyar'.",
    )
    parser.add_argument(
        "--keywords",
        nargs="*",
        default=None,
        help="Alternative positional keyword list.",
    )
    parser.add_argument(
        "--kesma-file",
        type=str,
        default="kesma_articles_r2",
        help="KESMA articles CSV base name (without extension).",
    )
    parser.add_argument(
        "--indep-file",
        type=str,
        default="indep_articles_r2",
        help="Independent articles CSV base name (without extension).",
    )
    parser.add_argument(
        "--text-column",
        type=str,
        default="text",
        help="Article text column name.",
    )
    args = parser.parse_args()

    keyword_group = args.keyword_group or " ".join(args.keywords or [])
    if not keyword_group:
        parser.error("Provide --keyword-group or positional keywords.")

    keywords = parse_keyword_group(keyword_group) if "," in keyword_group else (args.keywords or [keyword_group])
    outlet_scores = topic_comparison.keyword_group_outlet_scores(
        keywords,
        kesma_articles_file=args.kesma_file,
        indep_articles_file=args.indep_file,
        text_col=args.text_column,
    )

    print(json.dumps(outlet_scores, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
