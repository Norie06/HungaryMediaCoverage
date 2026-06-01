import pandas as pd
from pathlib import Path

base_dir = Path(__file__).resolve().parent
keywords_path = base_dir / "keywords_form.csv"
mapping_path = base_dir / "topic_mapping.csv"

# Load your data
keywords_df = pd.read_csv(keywords_path)
mapping_df = pd.read_csv(mapping_path)

# Add respondent ID per row before melting
keywords_df["respondent_id"] = range(1, len(keywords_df) + 1)

# Rename mapping key for a single merge key
mapping_df = mapping_df.rename(columns={"Topic_id": "topic_id", "Timestamp": "topic_column"})

# Determine which columns are actual topic items from the form
topic_cols = [col for col in keywords_df.columns if col in mapping_df["topic_column"].tolist()]

if not topic_cols:
    raise ValueError("No topic columns were found in keywords_form.csv that match topic_mapping.csv")

# Convert to long format
long_df = keywords_df.melt(
    id_vars=["respondent_id", "Timestamp"],
    value_vars=topic_cols,
    var_name="topic_column",
    value_name="rating"
)

# Drop missing values
long_df = long_df.dropna(subset=["rating"])

# Merge with your topic mapping table
final_df = long_df.merge(
    mapping_df,
    on="topic_column",
    how="left"
)

# Final columns
final_df = final_df[[
    "respondent_id",
    "topic_id",
    "Outlet group",
    "Source",
    "rating"
]]

# Save the result
output_path = base_dir / "keywords_form_long.csv"
final_df.to_csv(output_path, index=False)
print(f"Saved long-format data to {output_path}")