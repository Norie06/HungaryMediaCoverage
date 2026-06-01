from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent

DATASETS = {
    "Independent": BASE_DIR / "indep_topics_r2.csv",
    "KESMA": BASE_DIR / "kesma_topics_r2.csv",
}

OUT_PLOT = BASE_DIR / "r2_topic_counts.png"
TOP_N = 20

fig, axes = plt.subplots(1, 2, figsize=(18, 10), sharey=False)
fig.suptitle("Top BERTopic R2 article counts by topic", fontsize=16)

for ax, (label, csv_path) in zip(axes, DATASETS.items()):
    df = pd.read_csv(csv_path)
    df = df.sort_values("Count", ascending=False).head(TOP_N).reset_index(drop=True)

    topic_labels = df["Topic"].astype(str) + " | " + df["Name"].astype(str)
    counts = df["Count"]

    ax.barh(topic_labels, counts, color="#4C72B0")
    ax.set_title(label)
    ax.set_xlabel("Article count")
    ax.invert_yaxis()
    ax.tick_params(axis="y", labelrotation=0)
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    for idx, value in enumerate(counts):
        ax.text(value + max(counts) * 0.01, idx, str(int(value)), va="center")

fig.tight_layout(rect=(0, 0, 1, 0.96))
fig.savefig(OUT_PLOT, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Saved plot to: {OUT_PLOT}")
