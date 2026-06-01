"""
BERTopic Comparison: KESMA vs. Independent Outlets
====================================================
Compares topic coverage and keyword overlap/divergence
across two BERTopic rounds (r2 = first pass, r3 = deep-dive on topic 0).

Expected input files (place in same directory or set DATA_DIR):
    indep_topics_r2.csv, kesma_topics_r2.csv
    indep_articles_r2.csv, kesma_articles_r2.csv
    indep_topics_r3_t0.csv, kesma_topics_r3_t0.csv
    indep_articles_r3.csv, kesma_articles_r3.csv

Outputs (written to OUTPUT_DIR):
    coverage_r2.png / coverage_r3.png        — bar charts of article share per topic
    coverage_r2.csv / coverage_r3_t0.csv      — keyword-based topic coverage in both outlets
    keyword_overlap_r2.png / _r3.png         — Jaccard heatmap + Venn-style sets
    keyword_divergence_r2.csv / _r3.csv      — unique & shared keywords per topic pair
    summary_report.txt                        — human-readable summary
"""

import ast
import os
import re
import textwrap
import unicodedata
from pathlib import Path
from itertools import zip_longest

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec

# ── Configuration ────────────────────────────────────────────────────────────
DATA_DIR   = Path("bertopic_results")          # folder containing your CSV files
OUTPUT_DIR = Path("comparison_results")     # where plots & tables are saved
OUTPUT_DIR.mkdir(exist_ok=True)

# Column that holds the topic assignment in the articles files
ARTICLE_TOPIC_COL = "topic_r2"   # change to "topic" if needed for r3 files

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Cannot find {path}. Set DATA_DIR correctly.")
    return pd.read_csv(path)


def parse_representation(val) -> list[str]:
    """Convert the Representation column to a clean list of keyword strings."""
    if pd.isna(val):
        return []
    if isinstance(val, list):
        return [str(k).strip().lower() for k in val]
    try:
        parsed = ast.literal_eval(str(val))
        if isinstance(parsed, list):
            return [str(k).strip().lower() for k in parsed]
    except Exception:
        pass
    # fallback: comma-separated string
    return [k.strip().lower() for k in str(val).split(",") if k.strip()]


def keyword_sets(topics_df: pd.DataFrame) -> dict[int, set[str]]:
    """Return {topic_id: set_of_keywords} for every topic (excluding -1 = outlier)."""
    result = {}
    for _, row in topics_df.iterrows():
        tid = int(row["Topic"])
        if tid == -1:
            continue
        result[tid] = set(parse_representation(row["Representation"]))
    return result


def normalize_topic_value(value):
    """Normalize topic values from article files to integer topic IDs."""
    if pd.isna(value):
        return None
    if isinstance(value, str):
        if value.startswith("0_"):
            _, suffix = value.split("_", 1)
            try:
                return int(suffix)
            except ValueError:
                return None
        try:
            return int(value)
        except ValueError:
            return None
    if isinstance(value, (int, float, np.integer, np.floating)):
        if np.isnan(value):
            return None
        return int(value)
    return None


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def normalize_keyword_text(text: str) -> str:
    """Lowercase and strip accents so Hungarian keywords match article text."""
    value = str(text).strip().lower()
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def keyword_group_score(keywords: list[str],
                        kesma_articles_file: str = "kesma_articles_r2",
                        indep_articles_file: str = "indep_articles_r2",
                        text_col: str = "text") -> float:
    """
    Return a bounded score in [0,1] measuring proportional keyword coverage.

    Lower values mean the keyword group is more concentrated in KESMA articles
    relative to independent outlets, because the score is the independent share
    of the combined coverage.
    """
    cleaned_keywords = [normalize_keyword_text(k) for k in keywords if str(k).strip()]
    if not cleaned_keywords:
        raise ValueError("At least one keyword is required.")

    kesma_df = load_csv(kesma_articles_file)
    indep_df = load_csv(indep_articles_file)

    patterns = [re.compile(rf"(?<!\\w){re.escape(keyword)}(?!\\w)")
                for keyword in cleaned_keywords]

    def article_hits(df: pd.DataFrame) -> int:
        text_series = df[text_col].fillna("").astype(str).map(normalize_keyword_text)
        hits = pd.Series(False, index=df.index)
        for pattern in patterns:
            hits = hits | text_series.str.contains(pattern, regex=True, na=False)
        return int(hits.sum())

    kesma_hits = article_hits(kesma_df)
    indep_hits = article_hits(indep_df)

    kesma_rate = kesma_hits / max(len(kesma_df), 1)
    indep_rate = indep_hits / max(len(indep_df), 1)
    total_coverage = kesma_rate + indep_rate

    if total_coverage == 0:
        return 0.5

    return float(indep_rate / total_coverage)


def keyword_group_outlet_scores(keywords: list[str],
                                kesma_articles_file: str = "kesma_articles_r2",
                                indep_articles_file: str = "indep_articles_r2",
                                text_col: str = "text") -> dict[str, float]:
    """Return article-match proportions for each outlet for a keyword group."""
    cleaned_keywords = [normalize_keyword_text(k) for k in keywords if str(k).strip()]
    if not cleaned_keywords:
        raise ValueError("At least one keyword is required.")

    kesma_df = load_csv(kesma_articles_file)
    indep_df = load_csv(indep_articles_file)

    patterns = [re.compile(rf"(?<!\w){re.escape(keyword)}(?!\w)")
                for keyword in cleaned_keywords]

    def article_hits(df: pd.DataFrame) -> int:
        text_series = df[text_col].fillna("").astype(str).map(normalize_keyword_text)
        hits = pd.Series(False, index=df.index)
        for pattern in patterns:
            hits = hits | text_series.str.contains(pattern, regex=True, na=False)
        return int(hits.sum())

    kesma_hits = article_hits(kesma_df)
    indep_hits = article_hits(indep_df)

    return {
        "kesma": float(kesma_hits / max(len(kesma_df), 1)),
        "independent": float(indep_hits / max(len(indep_df), 1)),
    }


def keyword_group_outlet_coverages(keywords: list[str],
                                   kesma_df: pd.DataFrame,
                                   indep_df: pd.DataFrame,
                                   text_col: str = "text") -> dict[str, object]:
    """Return hit counts and coverage proportions for a keyword group across outlets."""
    cleaned_keywords = [normalize_keyword_text(k) for k in keywords if str(k).strip()]
    if not cleaned_keywords:
        return {
            "kesma_hits": 0,
            "independent_hits": 0,
            "kesma": 0.0,
            "independent": 0.0,
        }

    patterns = [re.compile(rf"(?<!\w){re.escape(keyword)}(?!\w)")
                for keyword in cleaned_keywords]

    def article_hits(df: pd.DataFrame) -> int:
        text_series = df[text_col].fillna("").astype(str).map(normalize_keyword_text)
        hits = pd.Series(False, index=df.index)
        for pattern in patterns:
            hits = hits | text_series.str.contains(pattern, regex=True, na=False)
        return int(hits.sum())

    kesma_hits = article_hits(kesma_df)
    indep_hits = article_hits(indep_df)

    return {
        "kesma_hits": kesma_hits,
        "independent_hits": indep_hits,
        "kesma": float(kesma_hits / max(len(kesma_df), 1)),
        "independent": float(indep_hits / max(len(indep_df), 1)),
    }


def coverage_df(articles: pd.DataFrame, topics: pd.DataFrame,
                topic_col: str) -> pd.DataFrame:
    """Return a DataFrame with columns [Topic, Name, ArticleCount, Pct] sorted by ArticleCount desc."""
    df = articles.copy()
    df["_topic_norm"] = df[topic_col].map(normalize_topic_value)

    known_topics = set(topics["Topic"].dropna().astype(int).tolist())

    valid = df[df["_topic_norm"].isin(known_topics) & (df["_topic_norm"] != -1)].copy()
    counts = valid["_topic_norm"].value_counts().reset_index()
    counts.columns = ["Topic", "ArticleCount"]
    counts["Pct"] = counts["ArticleCount"] / len(valid) * 100

    name_map = topics.set_index("Topic")["Name"].to_dict()
    counts["Name"] = counts["Topic"].map(name_map).fillna("Unknown")
    counts["Topic"] = counts["Topic"].astype(int)
    return counts.sort_values("ArticleCount", ascending=False).reset_index(drop=True)


def short_name(name: str, max_len: int = 40) -> str:
    """Truncate long topic names for axis labels.

    Use a safe truncation that preserves the start of the string. Replace
    underscores with spaces so keyword lists (which use underscores) are
    displayed as words. Falls back to a single-line slice when needed to
    avoid returning only an ellipsis when the first token is long.
    """
    if name is None:
        return ""
    s = str(name)
    # replace underscores with spaces to create word boundaries
    s = s.replace("_", " ")
    if len(s) <= max_len:
        return s
    # prefer cutting cleanly at max_len-1 and append ellipsis
    return s[: max_len - 1].rstrip() + "…"


# ── Plot 1: Coverage bar charts ───────────────────────────────────────────────

def plot_coverage(cov_kesma: pd.DataFrame, cov_indep: pd.DataFrame,
                  round_label: str, top_n: int | None = None):
    """Side-by-side horizontal bar charts of topic coverage (%)."""

    k = cov_kesma.head(top_n).copy()
    i = cov_indep.head(top_n).copy()
    n_rows = max(len(k), len(i))

    fig, axes = plt.subplots(1, 2, figsize=(18, max(6, n_rows * 0.35)),
                              sharey=False, facecolor="#f8f8f8")
    label_suffix = f" (top {top_n} topics)" if top_n is not None else " (all topics)"
    fig.suptitle(f"Topic Coverage — {round_label}{label_suffix}",
                 fontsize=14, fontweight="bold", y=1.01)

    for ax, df, color, title in zip(
        axes,
        [k, i],
        ["#1f6aa5", "#c0392b"],
        ["KESMA outlets", "Independent outlets"]
    ):
        labels = [short_name(n) for n in df["Name"]]
        bars = ax.barh(labels, df["Pct"], color=color, alpha=0.82, edgecolor="white")
        ax.set_xlabel("% of articles", fontsize=10)
        ax.set_title(title, fontsize=12, fontweight="bold", color=color)
        ax.invert_yaxis()
        ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=8)
        ax.set_xlim(0, df["Pct"].max() * 1.2)
        ax.grid(axis="x", linestyle="--", alpha=0.4)
        ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    out = OUTPUT_DIR / f"coverage_{round_label}.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out}")


def export_coverage_csv(kesma_topics: pd.DataFrame,
                        indep_topics: pd.DataFrame,
                        kesma_articles: pd.DataFrame,
                        indep_articles: pd.DataFrame,
                        round_label: str) -> pd.DataFrame:
    """Export topic coverage by keyword matching in both outlet article sets."""
    rows = []
    for outlet_label, topics_df in [("KESMA", kesma_topics), ("Independent", indep_topics)]:
        for _, row in topics_df.iterrows():
            topic_id = int(row["Topic"])
            if topic_id == -1:
                continue
            keywords = parse_representation(row["Representation"])
            coverages = keyword_group_outlet_coverages(keywords, kesma_articles, indep_articles)
            rows.append({
                "topic_source": outlet_label,
                "Topic": topic_id,
                "Name": row.get("Name", ""),
                "ArticleCount_kesma": coverages["kesma_hits"],
                "Pct_kesma": coverages["kesma"],
                "ArticleCount_indep": coverages["independent_hits"],
                "Pct_indep": coverages["independent"],
                "keywords": ", ".join(sorted(set(normalize_keyword_text(k) for k in keywords if str(k).strip())))
            })

    df = pd.DataFrame(rows)
    out = OUTPUT_DIR / f"coverage_{round_label}.csv"
    df.to_csv(out, index=False)
    print(f"  Saved: {out}")
    return df


def export_coverage_comparison_csv(cov_kesma: pd.DataFrame,
                                   cov_indep: pd.DataFrame,
                                   round_label: str) -> pd.DataFrame:
    """Export a combined coverage CSV with both outlet values side-by-side."""
    k = cov_kesma.copy().rename(columns={
        "Name": "Name_kesma",
        "ArticleCount": "ArticleCount_kesma",
        "Pct": "Pct_kesma"
    })
    i = cov_indep.copy().rename(columns={
        "Name": "Name_indep",
        "ArticleCount": "ArticleCount_indep",
        "Pct": "Pct_indep"
    })
    df = pd.merge(k, i, on="Topic", how="outer")
    out = OUTPUT_DIR / f"coverage_{round_label}_comparison.csv"
    df.to_csv(out, index=False)
    print(f"  Saved: {out}")
    return df


# ── Plot 2: Keyword overlap heatmap ──────────────────────────────────────────

def plot_keyword_heatmap(kw_kesma: dict[int, set], kw_indep: dict[int, set],
                         topics_kesma: pd.DataFrame, topics_indep: pd.DataFrame,
                         round_label: str, top_n: int | None = None):
    """
    Heatmap of Jaccard similarity between every pair of
    (KESMA topic, Independent topic).
    """
    k_ids = sorted(kw_kesma.keys())[:top_n]
    i_ids = sorted(kw_indep.keys())[:top_n]

    k_name = {tid: short_name(topics_kesma.set_index("Topic")["Name"].get(tid, str(tid)), 35)
              for tid in k_ids}
    i_name = {tid: short_name(topics_indep.set_index("Topic")["Name"].get(tid, str(tid)), 35)
              for tid in i_ids}

    matrix = np.array([[jaccard(kw_kesma[k], kw_indep[i])
                        for i in i_ids] for k in k_ids])

    fig, ax = plt.subplots(figsize=(max(10, len(i_ids) * 0.8),
                                    max(8,  len(k_ids) * 0.6)),
                            facecolor="#f8f8f8")
    im = ax.imshow(matrix, cmap="YlOrRd", vmin=0, vmax=1, aspect="auto")
    plt.colorbar(im, ax=ax, label="Jaccard similarity", shrink=0.7)

    xtick_fontsize = max(5, min(10, int(150 / max(1, len(i_ids)))))
    ytick_fontsize = max(5, min(10, int(150 / max(1, len(k_ids)))))

    ax.set_xticks(range(len(i_ids)))
    ax.set_xticklabels([i_name[t] for t in i_ids], rotation=45, ha="right", fontsize=xtick_fontsize)
    ax.set_yticks(range(len(k_ids)))
    ax.set_yticklabels([k_name[t] for t in k_ids], fontsize=ytick_fontsize)
    ax.set_xlabel("Independent topics", fontsize=10)
    ax.set_ylabel("KESMA topics", fontsize=10)
    ax.set_title(f"Keyword Jaccard Similarity — {round_label}", fontsize=13,
                 fontweight="bold")

    # annotate cells with value
    for r in range(len(k_ids)):
        for c in range(len(i_ids)):
            val = matrix[r, c]
            if val > 0:
                ax.text(c, r, f"{val:.2f}", ha="center", va="center",
                        fontsize=6.5,
                        color="black" if val < 0.6 else "white")

    plt.tight_layout()
    out = OUTPUT_DIR / f"keyword_overlap_{round_label}.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out}")

    return matrix, k_ids, i_ids


# ── Plot 3: Top keyword divergence per best-matched topic pair ────────────────

def plot_divergence_bars(kw_kesma: dict[int, set], kw_indep: dict[int, set],
                         topics_kesma: pd.DataFrame, topics_indep: pd.DataFrame,
                         matrix: np.ndarray, k_ids: list, i_ids: list,
                         round_label: str, top_pairs: int = 5):
    """
    For the top-N most similar topic pairs, show a side-by-side bar chart of:
      - keywords unique to KESMA   (left, blue)
      - keywords unique to Indep   (right, red)
      - keywords shared            (center, grey)
    """
    # find top pairs by Jaccard
    flat = [(matrix[r, c], k_ids[r], i_ids[c])
            for r in range(len(k_ids)) for c in range(len(i_ids))]
    flat.sort(reverse=True)
    top = flat[:top_pairs]

    k_names = topics_kesma.set_index("Topic")["Name"].to_dict()
    i_names = topics_indep.set_index("Topic")["Name"].to_dict()

    fig, axes = plt.subplots(top_pairs, 1,
                              figsize=(14, top_pairs * 3.5),
                              facecolor="#f8f8f8")
    if top_pairs == 1:
        axes = [axes]

    fig.suptitle(f"Keyword Divergence — Top {top_pairs} matched pairs ({round_label})",
                 fontsize=13, fontweight="bold")

    for ax, (score, kid, iid) in zip(axes, top):
        k_kw = kw_kesma.get(kid, set())
        i_kw = kw_indep.get(iid, set())
        shared   = sorted(k_kw & i_kw)
        only_k   = sorted(k_kw - i_kw)
        only_i   = sorted(i_kw - k_kw)

        # build x-axis: shared | only_kesma | only_indep
        groups   = shared + only_k + only_i
        colors   = (["#7f8c8d"] * len(shared) +
                    ["#1f6aa5"] * len(only_k) +
                    ["#c0392b"] * len(only_i))
        x        = range(len(groups))
        ax.bar(x, [1] * len(groups), color=colors, edgecolor="white", alpha=0.85)
        ax.set_xticks(list(x))
        ax.set_xticklabels(groups, rotation=60, ha="right", fontsize=7.5)
        ax.set_yticks([])

        k_label = short_name(k_names.get(kid, str(kid)), 45)
        i_label = short_name(i_names.get(iid, str(iid)), 45)
        ax.set_title(
            f"KESMA: {k_label}  ↔  Indep: {i_label}  (Jaccard={score:.2f})",
            fontsize=9, fontweight="bold")

        patches = [
            mpatches.Patch(color="#7f8c8d", label=f"Shared ({len(shared)})"),
            mpatches.Patch(color="#1f6aa5", label=f"KESMA only ({len(only_k)})"),
            mpatches.Patch(color="#c0392b", label=f"Indep only ({len(only_i)})"),
        ]
        ax.legend(handles=patches, loc="upper right", fontsize=8)
        ax.spines[["top", "right", "left"]].set_visible(False)

    plt.tight_layout()
    out = OUTPUT_DIR / f"keyword_divergence_{round_label}.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out}")


# ── CSV export: full keyword overlap table ────────────────────────────────────

def export_divergence_csv(kw_kesma: dict[int, set], kw_indep: dict[int, set],
                           topics_kesma: pd.DataFrame, topics_indep: pd.DataFrame,
                           round_label: str):
    """Export a CSV with every topic pair and their shared / unique keywords."""
    k_names = topics_kesma.set_index("Topic")["Name"].to_dict()
    i_names = topics_indep.set_index("Topic")["Name"].to_dict()

    rows = []
    for kid, k_kw in kw_kesma.items():
        for iid, i_kw in kw_indep.items():
            shared  = k_kw & i_kw
            only_k  = k_kw - i_kw
            only_i  = i_kw - k_kw
            j       = jaccard(k_kw, i_kw)
            rows.append({
                "kesma_topic_id":    kid,
                "kesma_topic_name":  k_names.get(kid, ""),
                "indep_topic_id":    iid,
                "indep_topic_name":  i_names.get(iid, ""),
                "jaccard":           round(j, 4),
                "n_shared":          len(shared),
                "n_kesma_only":      len(only_k),
                "n_indep_only":      len(only_i),
                "shared_keywords":   ", ".join(sorted(shared)),
                "kesma_only_keywords": ", ".join(sorted(only_k)),
                "indep_only_keywords": ", ".join(sorted(only_i)),
            })

    df = pd.DataFrame(rows).sort_values("jaccard", ascending=False)
    out = OUTPUT_DIR / f"keyword_divergence_{round_label}.csv"
    df.to_csv(out, index=False)
    print(f"  Saved: {out}")
    return df


# ── Text summary ──────────────────────────────────────────────────────────────

def write_summary(cov_k2, cov_i2, div_r2, cov_k3, cov_i3, div_r3):
    lines = []
    add = lines.append

    add("=" * 70)
    add("TOPIC COMPARISON SUMMARY: KESMA vs. INDEPENDENT OUTLETS")
    add("=" * 70)

    for label, ck, ci, div in [("ROUND 2 (first-pass topics)", cov_k2, cov_i2, div_r2),
                                 ("ROUND 3 (deep-dive on KESMA topic 0)", cov_k3, cov_i3, div_r3)]:
        add(f"\n{'─'*60}")
        add(f"  {label}")
        add(f"{'─'*60}")

        add("\n  Top 5 topics by coverage:")
        add(f"  {'KESMA':40s}  {'Independent':40s}")
        for (_, kr), (_, ir) in zip_longest(ck.head(5).iterrows(),
                                              ci.head(5).iterrows(),
                                              fillvalue=(None, pd.Series())):
            kn = short_name(kr.get("Name","—"), 38) if kr is not None else "—"
            in_ = short_name(ir.get("Name","—"), 38) if ir is not None else "—"
            kp = f"({kr['Pct']:.1f}%)" if kr is not None and "Pct" in kr else ""
            ip = f"({ir['Pct']:.1f}%)" if ir is not None and "Pct" in ir else ""
            add(f"  {kn+' '+kp:40s}  {in_+' '+ip:40s}")

        top5 = div.head(5)
        add("\n  Top 5 most similar topic pairs (by Jaccard keyword overlap):")
        for _, row in top5.iterrows():
            add(f"  [{row['jaccard']:.2f}]  KESMA: {short_name(row['kesma_topic_name'],35)}"
                f"  ↔  Indep: {short_name(row['indep_topic_name'],35)}")
            add(f"         Shared ({row['n_shared']}): {row['shared_keywords'][:80]}")
            add(f"         KESMA only ({row['n_kesma_only']}): {row['kesma_only_keywords'][:80]}")
            add(f"         Indep only ({row['n_indep_only']}): {row['indep_only_keywords'][:80]}")

    add("\n" + "=" * 70)
    report = "\n".join(lines)
    out = OUTPUT_DIR / "summary_report.txt"
    out.write_text(report, encoding="utf-8")
    print(f"  Saved: {out}")
    print("\n" + report)


# ── Main ──────────────────────────────────────────────────────────────────────

def run_round(round_label: str,
              kesma_topics_file: str, indep_topics_file: str,
              kesma_articles_file: str, indep_articles_file: str,
              topic_col: str):

    print(f"\n{'='*60}")
    print(f"  Processing: {round_label}")
    print(f"{'='*60}")

    kt = load_csv(kesma_topics_file)
    it = load_csv(indep_topics_file)
    ka = load_csv(kesma_articles_file)
    ia = load_csv(indep_articles_file)

    # ── Coverage ──────────────────────────────────────────────────────────────
    cov_k = coverage_df(ka, kt, topic_col)
    cov_i = coverage_df(ia, it, topic_col)
    plot_coverage(cov_k, cov_i, round_label)
    export_coverage_csv(kt, it, ka, ia, round_label)
    export_coverage_comparison_csv(cov_k, cov_i, round_label)

    # ── Keyword sets ──────────────────────────────────────────────────────────
    kw_k = keyword_sets(kt)
    kw_i = keyword_sets(it)

    # ── Heatmap ───────────────────────────────────────────────────────────────
    matrix, k_ids, i_ids = plot_keyword_heatmap(kw_k, kw_i, kt, it, round_label)

    # ── Divergence bars ───────────────────────────────────────────────────────
    plot_divergence_bars(kw_k, kw_i, kt, it, matrix, k_ids, i_ids, round_label)

    # ── CSV export ────────────────────────────────────────────────────────────
    div_df = export_divergence_csv(kw_k, kw_i, kt, it, round_label)

    return cov_k, cov_i, div_df


def main():
    # ── Round 2 ───────────────────────────────────────────────────────────────
    cov_k2, cov_i2, div_r2 = run_round(
        round_label          = "r2",
        kesma_topics_file    = "kesma_topics_r2",
        indep_topics_file    = "indep_topics_r2",
        kesma_articles_file  = "kesma_articles_r2",
        indep_articles_file  = "indep_articles_r2",
        topic_col            = "topic_r2",
    )

    # ── Round 3 (deep-dive on topic 0) ────────────────────────────────────────
    # For articles_r3, the topic column is topic_r3 and needs normalization.
    ARTICLE_TOPIC_COL_R3 = "topic_r3"

    cov_k3, cov_i3, div_r3 = run_round(
        round_label          = "r3_t0",
        kesma_topics_file    = "kesma_topics_r3_t0",
        indep_topics_file    = "indep_topics_r3_t0",
        kesma_articles_file  = "kesma_articles_r3",
        indep_articles_file  = "indep_articles_r3",
        topic_col            = ARTICLE_TOPIC_COL_R3,
    )

    # ── Summary report ────────────────────────────────────────────────────────
    write_summary(cov_k2, cov_i2, div_r2, cov_k3, cov_i3, div_r3)

    print(f"\n✓ All outputs written to: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()