import scipy.stats as stats
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

base_dir = Path(__file__).resolve().parent
csv_path = base_dir / "keywords_form_long.csv"
plot_path = base_dir / "rating_boxplot.png"

long_df = pd.read_csv(csv_path)
final_df = long_df.dropna(subset=["rating"])

kesma = final_df[final_df["Outlet group"] == "KESMA"]["rating"]
indep = final_df[final_df["Outlet group"] == "Independent"]["rating"]

summary = final_df.groupby("Outlet group")["rating"].describe()
print("Rating summary by Outlet group:\n")
print(summary)
print()

# Use Welch's t-test by default to avoid assuming equal variances
t_test = stats.ttest_ind(kesma, indep, equal_var=False)
print("Two-sample t-test (Welch) result:")
print(f"  statistic: {t_test.statistic:.4f}")
print(f"  p-value:   {t_test.pvalue:.4g}")
print(f"  df:        {t_test.df:.4f}" if hasattr(t_test, 'df') else "  df:        not available")

# Boxplot of rating distributions by outlet group
fig, ax = plt.subplots(figsize=(8, 6))
final_df.boxplot(column="rating", by="Outlet group", ax=ax, grid=False, patch_artist=True)
ax.set_title("Rating distribution by Outlet group")
ax.set_xlabel("Outlet group")
ax.set_ylabel("Rating")
plt.suptitle("")
plt.tight_layout()
plt.savefig(plot_path)
plt.close(fig)
print(f"Saved box plot to {plot_path}")
